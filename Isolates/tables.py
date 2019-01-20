from django_tables2 import tables, Column, LinkColumn, A, ManyToManyColumn, URLColumn, TemplateColumn

from Isolates.models import Isolate, AroGene, RastResult


class IsolateTable(tables.Table):
    species = LinkColumn('species-view', kwargs={'rank': 'name', 'name': A('species')})
    identifier = LinkColumn()

    class Meta:
        model = Isolate
        exclude = ['resistance', 'susceptibility', 'id']
        template_name = 'django_tables2/bootstrap4.html'
        attrs = {'class': 'table  table-bordered'}


class AroGeneTable(tables.Table):
    # aro_category = ManyToManyColumn()
    aro_name = TemplateColumn('<a href="https://card.mcmaster.ca/ontology/{{record.aro_id}}">{{record.aro_name}}  (ARO:{{record.aro_accession}})</a>')

    class Meta:
        model = AroGene
        fields=['aro_name', 'model_type', 'aro_description']
        # exclude = ['model_id', 'model_type_id', 'aro_id', 'model_description', 'model_name']
        template_name = 'django_tables2/bootstrap4.html'
        attrs = {'class': 'table  table-bordered'}

class RastResultTable(tables.Table):

    class Meta:
        model = RastResult
        exclude = []
        template_name = 'django_tables2/bootstrap4.html'
        attrs = {'class': 'table  table-bordered'}


