from django.contrib import admin, messages

# Register your models here.
from Isolates.models import Isolate, Species, Patient, Sample, Sequence, AntibioticTest, AroCategory, \
    AroGeneMatch, AroGene, Result, HumanOntologyTerm, OntologyTerm, ReferenceSpecies


class IsolateAdmin(admin.ModelAdmin):
    list_filter = ['collection_date']
    search_fields = ['species__name']
    list_display = ('collection_date', 'species', 'samples')
    readonly_fields = ('samples',)

    def samples(self, obj):
        return obj.get_samples_names()


class AroGeneAdmin(admin.ModelAdmin):
    list_display = [
        'model_id',
        'model_name',
        'model_type',
        'model_type_id',
        'model_description',
        'aro_accession',
        'aro_id',
        'aro_name',
        'aro_description'
    ]

class AroCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'category_aro_accession',
        'category_aro_cvterm_id',
        'category_aro_name',
        'category_aro_description',
        'category_aro_class_name',
    ]


class ReferenceSpeciesAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'genus',
        'family',
        'order',
        'klass',
        'phylum',
        'kingdom'
    ]
    search_fields = ['name']

    actions = ['enable_species']

    def enable_species(self, request, queryset):
        for rs in queryset:
            try:
                rs.copy_to_species()
                self.message_user(
                    request=request,
                    message='Species {} has been copied'.format(
                        rs.name
                    ),
                    level=messages.SUCCESS
                )
            except:
                self.message_user(
                    request=request,
                    message='Species {} has not been copied'.format(
                        rs.name
                    ),
                    level=messages.ERROR
                )


class AroGeneMatchAdmin(admin.ModelAdmin):
    list_display = [
        'result',
        'aro_gene',
        'identifier',
        'contig',
        'type_match',
        'orf_strand',
        'orf_start',
        'orf_end',
        'orf_from',
        'pass_evalue',
        'pass_bitscore',
        'evalue',
        'max_identities',
        'bit_score',
        'cvterm_id',
        'query',
        'match',
        'sequence_from_db',
        'sequence_from_broadstreet',
        'dna_sequence_from_broadstreet',
        'query_start',
        'query_end',
        'orf_dna_sequence',
        'orf_prot_sequence',
        'perc_identity',
    ]


def run_pipeline(modeladmin, request, queryset):
    for i in queryset:
        try:
            i.run_pipeline()
            admin.ModelAdmin.message_user(modeladmin, request, 'Sent Pipeline for sequence: {}'.format(i.identifier),
                                          messages.INFO)
        except Exception as e:
            admin.ModelAdmin.message_user(modeladmin,
                                          request,
                                          'Failed sending Pipeline for sequence: {}/ Reason {}'.format(i.identifier, e),
                                          messages.ERROR
                                          )


class SequenceAdmin(admin.ModelAdmin):
    list_display = ['sample', 'identifier', 'sequence_file_pair1', 'sequence_file_pair2']
    actions = [run_pipeline]

admin.site.register(Isolate, IsolateAdmin)
admin.site.register(Species)
admin.site.register(ReferenceSpecies, ReferenceSpeciesAdmin)
admin.site.register(Patient)
admin.site.register(Sample)
admin.site.register(Sequence, SequenceAdmin)
admin.site.register(AntibioticTest)
admin.site.register(AroGeneMatch, AroGeneMatchAdmin)
admin.site.register(AroGene, AroGeneAdmin)
admin.site.register(AroCategory, AroCategoryAdmin)
admin.site.register(Result)
admin.site.register(HumanOntologyTerm)
admin.site.register(OntologyTerm)