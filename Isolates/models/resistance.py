import random

from django.db import models
from django.db.models import Count

from Isolates.models.result import Result


class AroCategory(models.Model):
    CATEGORIES = (
        ('AMR Gene Family', 'AMR Gene Family'),
        ('Resistance Mechanism', 'Resistance Mechanism'),
        ('Efflux Regulator', 'Efflux Regulator'),
        ('Antibiotic', 'Antibiotic'),
        ('Adjuvant', 'Adjuvant'),
        ('Efflux Component', 'Efflux Component'),
        ('Drug Class', 'Drug Class'),
    )
    category_aro_accession = models.CharField(max_length=250, editable=False, unique=True)
    category_aro_cvterm_id = models.CharField(max_length=250, editable=False)
    category_aro_name = models.CharField(max_length=250, editable=False)
    category_aro_description = models.CharField(max_length=2500, editable=False)
    category_aro_class_name = models.CharField(max_length=250, editable=False, choices=CATEGORIES)

    def __str__(self):
        return self.category_aro_name


class AroGene(models.Model):
    model_id = models.CharField(max_length=250, editable=False, unique=True, primary_key=True)
    model_name = models.CharField(max_length=250, editable=False)
    model_type = models.CharField(max_length=250, editable=False)
    model_type_id = models.CharField(max_length=250, editable=False)
    model_description = models.CharField(max_length=2500, editable=False)
    aro_accession = models.CharField(max_length=250, editable=False)
    aro_id = models.CharField(max_length=250, editable=False)
    aro_name = models.CharField(max_length=2500, editable=False)
    aro_description = models.CharField(max_length=2500, editable=False)
    aro_category = models.ManyToManyField(AroCategory, related_name='aro_gene', editable=False)


class AroGeneMatch(models.Model):

    TYPE_MATCH = (('Loose', 'Loose'),
                  ('Perfect', 'Perfect'),
                  ('Strict', 'Strict')
                  )

    result = models.ForeignKey(Result, related_query_name='genes', related_name='result', on_delete=models.CASCADE)
    aro_gene = models.ForeignKey(AroGene, related_name='result', on_delete=models.PROTECT)
    identifier = models.CharField(max_length=2555)
    contig = models.CharField(max_length=255)
    type_match = models.CharField(editable=False, choices=TYPE_MATCH, max_length=10)
    orf_strand = models.CharField(max_length=1, editable=False)
    orf_start = models.IntegerField(editable=False)
    orf_end = models.IntegerField(editable=False)
    orf_from = models.CharField(editable=False, max_length=2500)
    pass_evalue = models.CharField(editable=False, max_length=255)
    pass_bitscore = models.CharField(editable=False, max_length=255)
    evalue = models.FloatField(editable=False)
    max_identities = models.IntegerField(editable=False)
    bit_score = models.FloatField(editable=False)
    cvterm_id = models.CharField(editable=False, max_length=255)
    query = models.CharField(editable=False, max_length=5000)
    match = models.CharField(editable=False, max_length=5000)
    sequence_from_db = models.CharField(editable=False, max_length=5000)
    sequence_from_broadstreet = models.CharField(editable=False, max_length=5000)
    dna_sequence_from_broadstreet = models.CharField(editable=False, max_length=5000)
    query_start = models.IntegerField(editable=False)
    query_end = models.IntegerField(editable=False)
    orf_dna_sequence = models.CharField(editable=False, max_length=5000)
    orf_prot_sequence = models.CharField(editable=False, max_length=5000)
    perc_identity = models.FloatField(editable=False)
    nudged = models.BooleanField(editable=False, default=False)

    @classmethod
    def from_rgi_result(cls, contig_hits, result):
        hit = sorted(contig_hits.values(), key=lambda k: k['bit_score'])[-1]
        contig = hit['orf_from']
        aro_gene = AroGene.objects.get(model_id=hit['model_id'])
        creation_values = {key.lower(): hit[key]
                           for key in hit if key.lower() in [f.name for f in cls._meta.fields]
                           }
        print (creation_values)
        cls.objects.create(contig=contig, aro_gene=aro_gene, result=result, **creation_values)


    @classmethod
    def from_rgi_result_randomize(cls, contig_hits, result):
        qs = AroGene.objects.all()
        hit = sorted(contig_hits.values(), key=lambda k: k['bit_score'])[-1]
        contig = hit['orf_from']
        aro_gene = qs[random.randint(0, qs.aggregate(count=Count('pk'))['count'] - 1)]
        creation_values = {key.lower(): hit[key]
                           for key in hit if key in [f.name for f in cls._meta.fields]
                           }
        cls.objects.create(contig=contig, aro_gene=aro_gene, result=result, **creation_values)