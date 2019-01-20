from django_filters import DateFilter, FilterSet, ModelChoiceFilter, ModelMultipleChoiceFilter

from Isolates.models import Isolate, AroCategory, OntologyTerm


def drug_class(request):
    if request is None:
        return AroCategory.objects.none()

    return AroCategory.objects.filter(category_aro_class_name='Drug Class')


def resistance_mechanism(request):
    if request is None:
        return AroCategory.objects.none()

    return AroCategory.objects.filter(category_aro_class_name='Resistance Mechanism')


def antibiotic(request):
    if request is None:
        return AroCategory.objects.none()

    return AroCategory.objects.filter(category_aro_class_name='Antibiotic')


def gene_family(request):
    if request is None:
        return AroCategory.objects.none()

    return AroCategory.objects.filter(category_aro_class_name='AMR Gene Family')


def get_terms(request):
    if request is None:
        return OntologyTerm.objects.none()

    return OntologyTerm.objects.filter(ontology='omp')


class IsolateFilter(FilterSet):

    drug_class = ModelMultipleChoiceFilter(queryset=drug_class, method='my_custom_filter',
                                           label='Drug Class (Resistance to)')
    antibiotic = ModelMultipleChoiceFilter(queryset=antibiotic, method='my_custom_filter',
                                           label='Antibiotic (Resistance to)')
    resistance_mechanism = ModelMultipleChoiceFilter(queryset=resistance_mechanism, method='my_custom_filter',
                                                     label='Resistance Mechanism')
    gene_family = ModelMultipleChoiceFilter(queryset=gene_family, method='my_custom_filter', label='AMR Gene Family')
    phenotype = ModelMultipleChoiceFilter(queryset=get_terms, method='filter_by_terms', label='Bacterial Pehnotypes')

    class Meta:
        model = Isolate
        exclude = ['resistance', 'susceptibility', 'id']

    def my_custom_filter(self, queryset, name, value):
        if value:
            return queryset.filter(sample__result__genes__aro_gene__aro_category__in=value).distinct()
        else:
            return queryset.filter()


    def filter_by_terms(self, queryset, name, values):
        if values:
            for value in values:
                queryset = queryset.filter(phenotype__ontology_term=value)
            return queryset.distinct()
        else:
            return queryset.filter()