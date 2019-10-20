from django.db import models


def sample_sequence_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<sample>/<sequence_id>/<filename>
    return 'reference_genomes/{0}/{1}'.format(instance.name, filename)


class ReferenceSpecies(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    genus = models.CharField(max_length=255, null=False, blank=False)
    family = models.CharField(max_length=255, null=False, blank=False)
    order = models.CharField(max_length=255, null=False, blank=False)
    klass = models.CharField(max_length=255, null=False, blank=False)
    phylum = models.CharField(max_length=255, null=False, blank=False)
    kingdom = models.CharField(max_length=255, null=False, blank=False)

    def copy_to_species(self):
        return Species.objects.update_or_create(name=self.name,
                                                defaults={
                                                    'genus': self.genus,
                                                    'family': self.family,
                                                    'order': self.order,
                                                    'klass': self.klass,
                                                    'phylum': self.phylum,
                                                    'kingdom': self.kingdom,
                                                })


class Species(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    genus = models.CharField(max_length=255, null=False, blank=False)
    family = models.CharField(max_length=255, null=False, blank=False)
    order = models.CharField(max_length=255, null=False, blank=False)
    klass = models.CharField(max_length=255, null=False, blank=False)
    phylum = models.CharField(max_length=255, null=False, blank=False)
    kingdom = models.CharField(max_length=255, null=False, blank=False)
    sequence_file = models.FileField(upload_to=sample_sequence_directory_path)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('isolate-list') + '?species={}'.format(self.pk)

    def create_from_ref(self, reference_species):
        """

        :type reference_species: ReferenceSpecies
        """
        return self.objects.update_or_create(name=reference_species.name,
                                             defaults={
                                                 'genus': reference_species.genus,
                                                 'family': reference_species.family,
                                                 'order': reference_species.order,
                                                 'klass': reference_species.klass,
                                                 'phylum': reference_species.phylum,
                                                 'kingdom': reference_species.kingdom,
                                             })[0]

    def __str__(self):
        return self.name