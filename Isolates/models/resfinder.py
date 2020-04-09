from django.db import models

from Isolates.models.result import Result


class ResistanceFactor(models.Model):
    resfinder_id = models.CharField(max_length=250, editable=False, primary_key=True)
    accession = models.CharField(max_length=250, editable=False)
    antibiotic = models.CharField(max_length=250, editable=False)
    resistance_gene = models.CharField(max_length=250, editable=False)
    predicted_phenotype = models.CharField(max_length=2500, editable=False, blank=True, null=True)


class ResistanceFactorHit(models.Model):
    result = models.ForeignKey(Result, related_name='resistance_factor_hit', on_delete=models.CASCADE)
    resistance_factor = models.ForeignKey(ResistanceFactor, related_name='resistance_factor_hit', on_delete=models.PROTECT)
    identifier = models.CharField(max_length=2555)
    contig = models.CharField(max_length=255)
    perc_identity = models.FloatField(editable=False)
    hsp_length = models.IntegerField(editable=False)
    template_length = models.IntegerField(editable=False)
    position_in_ref = models.CharField(max_length=255)
    positions_in_contig = models.CharField(max_length=255)


    @classmethod
    def from_resistance_finder_result(cls, hit, antibiotic, result, resfinder_id):
        rf, created = ResistanceFactor.objects.get_or_create(
                resfinder_id=resfinder_id,
                defaults=dict(
                    antibiotic=antibiotic,
                    resistance_gene=hit.get('resistance_gene'),
                    accession=hit.get('accession'),
                    predicted_phenotype=hit.get('predicted_phenotype')
                )
        )
        cls.objects.create(
            result=result,
            resistance_factor=rf,
            identifier=hit.get('hit_id'),
            contig=hit.get('contig_name'),
            perc_identity=float(hit.get('identity')),
            hsp_length=int(hit.get('HSP_length')),
            template_length=int(hit.get('template_length')),
            position_in_ref=hit.get('position_in_ref'),
            positions_in_contig=hit.get('positions_in_contig')
        )


