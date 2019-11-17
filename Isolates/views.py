from django.db.models import Count, Max, Min
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from Isolates.filtersets import IsolateFilter
from Isolates.forms import PatientForm, IsolateForm
from Isolates.models import Isolate, Species, AroGeneMatch, Patient, AroGene, RastResult, Sample, VirulenceFactorHit
from Isolates.plots import IsolatePlots, GeneMatchPlots
from Isolates.tables import IsolateTable, AroGeneTable, RastResultTable, VirulenceFinderTable
from bac_tasks.models import ComponentTask


class IsolateList(SingleTableMixin, FilterView):
    model = Isolate
    template_name = 'isolates_list/isolate_main.html'
    context_object_name = "isolate_list"
    filterset_class = IsolateFilter
    table_class = IsolateTable
    paginate_by = 15

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(IsolateList, self).get_context_data(**kwargs)
        plot_renderer = IsolatePlots(self.object_list)
        context['title'] = 'Isolates - BaC'
        context['species_count'] = plot_renderer.create_pie_plot('species__genus', 'Species')
        context['tissue_origin_count'] = plot_renderer.create_pie_plot('tissue_origin', 'Tissue')
        context['culture_type_count'] = plot_renderer.create_pie_plot('culture_type', 'Culture')
        return context


class GroupOverview(ListView):

    def get_queryset(self):
        pass

    def get_summary(self):
        summary = dict(
            aro_genes_count=self.object_list.count(),
            isolates_count=self.object_list.aggregate(count=Count('result__sample__isolate', distinct=True))['count'],
            first_collection=self.object_list.aggregate(date=Min('result__sample__isolate__collection_date'))['date'],
            last_collection=self.object_list.aggregate(date=Max('result__sample__isolate__collection_date'))['date'],
            number_of_samples=self.object_list.aggregate(count=Count('result__sample', distinct=True))['count'],
            number_of_sequences=self.object_list.aggregate(count=Count('result__sequences', distinct=True))['count'])
        summary['average_aro_gene_per_sample'] = summary['aro_genes_count'] / summary['isolates_count']
        return summary

    def get_aro_classes_summary(self, last_day, isolate_count):
        summary = {
            klass: self.object_list.filter(aro_gene__aro_category__category_aro_class_name=klass).values(
                'aro_gene__aro_category__category_aro_name').annotate(
                count=Count('result__sample__isolate', distinct=True),
                first=Min('result__sample__isolate__collection_date')).order_by('count', '-first') for klass in
            ['Resistance Mechanism', 'Drug Class', 'Antibiotic', 'AMR Gene Family', 'Adjuvant']
        }

        for category in summary:
            for item in summary[category]:
                if item['first'] == last_day:
                    item['new'] = True

                else:
                    item['new'] = False

                if item['count']/isolate_count < 0.05:
                    item['risk'] = True

                else:
                    item['risk'] = False

        return summary

    def get_alerts(self, aro_summary):
        new_items = {}
        for category in aro_summary:
            for item in aro_summary[category]:
                if item.get('new'):
                    item['category'] = category
                    new_items.setdefault(category, []).append(item)
        return new_items

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(GroupOverview, self).get_context_data(**kwargs)
        plot_render = GeneMatchPlots(self.object_list.filter(aro_gene__aro_category__category_aro_class_name='Drug Class'))
        context['history_plot'] = plot_render.create_history_plot()
        context['summary'] = self.get_summary()
        context['aro_summary'] = self.get_aro_classes_summary(context['summary']['last_collection'], context['summary']['isolates_count'])
        context['alerts'] = self.get_alerts(context['aro_summary'])
        context['name'] = 'Group View'
        context['title'] = '{} - BaC'.format(context['name'])
        return context


class SpeciesView(GroupOverview):
    template_name = 'isolate_group/group_summary.html'

    def get_queryset(self):
        return AroGeneMatch.objects.filter(
            **{'result__sample__isolate__species__' + self.kwargs['rank']: self.kwargs['name']}
        )

    def get_context_data(self, **kwargs):
        context = super(SpeciesView, self).get_context_data(**kwargs)
        rank = self.kwargs['rank']
        name = self.kwargs['name']
        context['rank'] = rank
        context['name'] = name
        context['title'] = '{} - BaC'.format(name)
        return context


class SelectGroupView(FilterView, GroupOverview):
    model = Isolate
    filterset_class = IsolateFilter
    template_name = 'isolate_group/group_summary.html'

    def get_context_data(self, **kwargs):
        self.object_list = AroGeneMatch.objects.filter(result__sample__isolate__in=self.object_list)
        context = super(SelectGroupView, self).get_context_data(**kwargs)
        return context


class PatientCreate(CreateView):
    model = Patient
    form_class = PatientForm
    template_name = 'crud/patient/patient_create_update.html'

    def get_context_data(self, **kwargs):
        context = super(PatientCreate, self).get_context_data(**kwargs)
        context['create'] = True
        return context


class PatientUpdate(UpdateView):
    model = Patient
    form_class = PatientForm
    context_object_name = 'patient'
    template_name = 'crud/patient/patient_create_update.html'

    def get_initial(self):
        initial = super(PatientUpdate, self).get_initial()
        initial['phenotypes'] = [(p.ontology_term.ontology, p.ontology_term.term_id) for p in self.object.phenotype.all()]
        return initial

    def get_form(self, **kwargs):
        form = super(PatientUpdate, self).get_form(**kwargs)
        form.fields.get('identifier').disabled = True
        return form


class IsolateCreate(CreateView):
    model = Isolate
    form_class = IsolateForm
    template_name = 'crud/isolate/isolate_create_update.html'

    def get_context_data(self, **kwargs):
        context = super(IsolateCreate, self).get_context_data(**kwargs)
        context['create'] = True
        return context


class IsolateUpdate(UpdateView):
    model = Isolate
    form_class = IsolateForm
    context_object_name = 'isolate'
    template_name = 'crud/isolate/isolate_create_update.html'

    def get_initial(self):
        initial = super(IsolateUpdate, self).get_initial()
        initial['phenotypes'] = [(p.ontology_term.ontology, p.ontology_term.term_id) for p in self.object.phenotype.all()]
        return initial

    def get_form(self, **kwargs):
        form = super(IsolateUpdate, self).get_form(**kwargs)
        form.fields.get('identifier').disabled = True
        return form


class IsolateDetail(DetailView):
    model = Isolate
    template_name_field = 'isolate'
    template_name = 'isolate_detail/isolate_details.html'

    def get_context_data(self, **kwargs):
        context = super(IsolateDetail, self).get_context_data(**kwargs)
        context['table'] = AroGeneTable(data=AroGene.objects.filter(result__result__sample__isolate=self.object))
        if self.object.samples.first().rast_folder:
            with open(self.object.samples.first().rast_folder + '/'+ self.object.samples.first().identifier + '.gff') as fd:
                fd.readline()
                r = [RastResult.from_gff_line(line) for line in fd]
                context['table2'] = RastResultTable(data=r)
                context['title'] = '{} - BaC'.format(self.object.identifier)

        return context


class SampleResult(DetailView):
    model = Sample
    template_name_field = 'sample'
    template_name = 'sample_tasks/rast_result.html'

    def get_template_names(self):
        print(self.kwargs['tool'])
        if self.kwargs['tool'] == 'ANNOTATION':
            return super(SampleResult, self).get_template_names()
        elif self.kwargs['tool'] == 'RESISTANCE_ANALYSIS':
            return 'sample_tasks/resistance_result.html'
        elif self.kwargs['tool'] == 'VIRULENCE_ANALYSIS':
            return 'sample_tasks/resistance_result.html'

    def get_table(self):
        table = None
        if self.kwargs['tool'] == 'RESISTANCE_ANALYSIS':
            table = AroGeneTable(data=AroGene.objects.filter(result__result__sample=self.object))
        elif self.kwargs['tool'] == 'VIRULENCE_ANALYSIS':
            table = VirulenceFinderTable(data=VirulenceFactorHit.objects.filter(result__sample=self.object))
        elif self.kwargs['tool'] == 'ANNOTATION':
            if self.object.rast_folder:
                with open(
                        self.object.rast_folder + '/' + self.object.identifier + '.gff') as fd:
                    fd.readline()
                    r = [RastResult.from_gff_line(line) for line in fd]
                    table = RastResultTable(data=r)

            else:
                table = RastResult(data=[])

        return table

    def get_context_data(self, **kwargs):
        context = super(SampleResult, self).get_context_data(**kwargs)
        context['table'] = self.get_table()
        context['title'] = '{} - BaC'.format(self.object.identifier)
        return context
