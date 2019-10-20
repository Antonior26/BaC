from django.db import models

from Isolates.models import Result


class VirulenceFactor(models.Model):
    virulence_factor_id = models.CharField(max_length=250, editable=False, primary_key=True)
    db_name = models.CharField(max_length=250, editable=False)
    name = models.CharField(max_length=250, editable=False)
    accession = models.CharField(max_length=250, editable=False)
    species = models.CharField(max_length=250, editable=False)
    protein_function = models.CharField(max_length=250, editable=False)
    ncbi_id = models.CharField(max_length=250, editable=False, blank=True, null=True)
    full_desc = models.CharField(max_length=2500, editable=False, blank=True, null=True)
    organism = models.CharField(max_length=250, editable=False, blank=True, null=True)
    tax_id = models.CharField(max_length=250, editable=False, blank=True, null=True)
    link_to_ncbi = models.CharField(max_length=2500, editable=False, blank=True, null=True)


class VirulenceFactorHit(models.Model):
    result = models.ForeignKey(Result, related_query_name='genes', related_name='result', on_delete=models.CASCADE)
    virulence_factor = models.ForeignKey(VirulenceFactor, related_name='result', on_delete=models.PROTECT)
    identifier = models.CharField(max_length=2555)
    contig = models.CharField(max_length=255)
    perc_identity = models.FloatField(editable=False)
    hsp_length = models.IntegerField(editable=False)
    template_length = models.IntegerField(editable=False)
    position_in_ref = models.CharField(max_length=255)
    positions_in_contig = models.CharField(max_length=255)


    @classmethod
    def from_virulence_finder_result(cls, hit, species, db_name, result):
        vf = VirulenceFactor.objects.get_or_create(
                virulence_factor_id=hit.get('contig_name'),
                defaults=dict(
                    db_name=db_name,
                    species=species,
                    name=hit.get('virulence_gene'),
                    accession=hit.get('accession'),
                    protein_function=hit.get('protein_function')
                )
        )
        cls.objects.create(
            result=result,
            virulence_factor=vf,
            identifier=hit.get('hit_id'),
            contig=hit.get('contig_name'),
            perc_identity=float(hit.get('identity')),
            hsp_length=int(hit.get('HSP_length')),
            template_length=int(hit.get('template_length')),
            position_in_ref=int(hit.get('position_in_ref')),
            positions_in_contig=int(hit.get('positions_in_contig'))
        )


