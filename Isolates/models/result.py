from django.db import models

from Isolates.models.isolates import Sample, Sequence


class Result(models.Model):
    date = models.DateTimeField(auto_now=True, editable=False)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, editable=False)
    sequences = models.ManyToManyField(Sequence, editable=False)
    type = models.CharField(max_length=250, null=True, blank=True)

    @classmethod
    def from_rgi_result(cls, all_hits, sample, sequences=()):
        from Isolates.models.resistance import AroGeneMatch
        result = cls.objects.create(sample=sample, type='RESISTANCE_ANALYSIS')
        for s in sequences:
            result.sequences.add(s)
        for contig_hits in all_hits:
            AroGeneMatch.from_rgi_result(all_hits[contig_hits], result)

    @classmethod
    def from_virulence_finder_result(cls, virulence_finder_result, sample, sequences=()):
        from Isolates.models.virulence import VirulenceFactorHit
        result = cls.objects.create(sample=sample, type='VIRULENCE_ANALYSIS')
        for s in sequences:
            result.sequences.add(s)
        virulence_finder_results_by_species = virulence_finder_result.get('virulencefinder', {}
                                                                          ).get('results', [])
        for species in virulence_finder_results_by_species:
            for db_name in virulence_finder_results_by_species[species]:
                if db_name != "No hit found":
                    for db_result in virulence_finder_results_by_species[species][db_name]:
                        VirulenceFactorHit.from_virulence_finder_result(
                            result=result,
                            hit=virulence_finder_results_by_species[species][db_name][db_result],
                            species=species,
                            db_name=db_name
                    )

    @classmethod
    def from_rgi_result_randomize(cls, all_hits, sample, sequences=()):
        from Isolates.models.resistance import AroGeneMatch
        result = cls.objects.create(sample=sample)
        for s in sequences:
            result.sequences.add(s)
        for contig_hits in all_hits:
            AroGeneMatch.from_rgi_result_randomize(all_hits[contig_hits], result)