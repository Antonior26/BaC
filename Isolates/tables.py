from django_tables2 import tables, LinkColumn, A, TemplateColumn, Column

from Isolates.models import Isolate, AroGene, RastResult, VirulenceFactorHit


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


class VirulenceFinderTable(tables.Table):
    # aro_category = ManyToManyColumn()
    # aro_name = TemplateColumn('<a href="https://card.mcmaster.ca/ontology/{{record.aro_id}}">{{record.aro_name}}  (ARO:{{record.aro_accession}})</a>')

    name = Column(accessor='virulence_factor.name')
    accession = Column(accessor='virulence_factor.accession')
    species = Column(accessor='virulence_factor.species')
    protein_function = Column(accessor='virulence_factor.protein_function')

    class Meta:
        model = VirulenceFactorHit
        fields = ['name', 'accession', 'species', 'protein_function', 'contig', 'perc_identity', 'hsp_length', 'template_length', 'position_in_ref',
                'positions_in_contig']
        # exclude = ['model_id', 'model_type_id', 'aro_id', 'model_description', 'model_name']
        template_name = 'django_tables2/bootstrap4.html'
        attrs = {'class': 'table  table-bordered'}


class RastResultTable(tables.Table):

    class Meta:
        model = RastResult
        exclude = []
        template_name = 'django_tables2/bootstrap4.html'
        attrs = {'class': 'table  table-bordered'}


