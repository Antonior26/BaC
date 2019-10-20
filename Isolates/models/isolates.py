import os

from celery import group
from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver
from django.urls import reverse

from Isolates.models import AntibioticTest
from Isolates.models.species import Species
from bac_tasks.tasks import run_component


def sequence_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<sample>/<sequence_id>/<filename>
    return 'sequence_results/{0}/{1}/{2}'.format(instance.sample, instance.identifier, filename)


def sample_sequence_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<sample>/<sequence_id>/<filename>
    return 'reference_genomes/{0}/{1}'.format(instance.name, filename)


def fq_validate_file_extension(value):
    valid_extensions = ['.fq.gz', '.fastq.gz']
    if not value.name.endswith('.fastq.gz') and not value.name.endswith('.fq.gz'):
        raise ValidationError(u'Unsupported file extension. Supported File extensions: {}'.format(
            ','.join(valid_extensions)
        ))


def fa_validate_file_extension(value):
    valid_extensions = ['.fa', '.fasta']
    if not value.name.endswith('.fa') and not value.name.endswith('.fasta'):
        raise ValidationError(u'Unsupported file extension. Supported File extensions: {}'.format(
            ','.join(valid_extensions)
        ))


class OntologyTerm(models.Model):
    ontology = models.CharField(max_length=255)
    term_id = models.CharField(max_length=255, primary_key=True)
    label = models.CharField(max_length=255)
    description = models.CharField(max_length=2555)

    def __str__(self):
        return '{} ({})'.format(self.label or self.term_id, self.ontology)

    def get_absolute_url(self):
        return 'https://www.ebi.ac.uk/ols/ontologies/{}/terms?iri=http://purl.obolibrary.org/obo/{}'.format(
            self.ontology.lower(), self.term_id.replace(':', '_')
        )


class Patient(models.Model):
    identifier = models.CharField(max_length=255, primary_key=True)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('isolate-list') + '?patient={}'.format(self.pk)

    def __str__(self):
        return str(self.identifier)


class HumanOntologyTerm(models.Model):
    ontology_term = models.ForeignKey(OntologyTerm, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='phenotype')


class Isolate(models.Model):
    identifier = models.CharField(max_length=255, primary_key=True)
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='species')
    collection_date = models.DateField()
    culture_type = models.CharField(max_length=255)
    tissue_origin = models.CharField(max_length=255)
    resistance = models.OneToOneField(AntibioticTest, related_name='resistances',
                                      on_delete=models.CASCADE, blank=True, null=True, editable=False)
    susceptibility = models.OneToOneField(AntibioticTest, related_name='susceptibilies',
                                          on_delete=models.CASCADE, blank=True, null=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    class Meta:
        ordering = ['collection_date']

    def get_samples_names(self):
        return [s.identifier for s in self.samples.all()]

    def get_absolute_url(self):
        return reverse('isolate-detail-view', kwargs={'pk': self.pk})

    def __str__(self):
        return self.identifier


class BacteriaOntologyTerm(models.Model):
    ontology_term = models.ForeignKey(OntologyTerm, on_delete=models.CASCADE)
    isolate = models.ForeignKey(Isolate, on_delete=models.CASCADE, related_name='phenotype')


class Sample(models.Model):
    identifier = models.CharField(max_length=255, primary_key=True)
    isolate = models.ForeignKey(Isolate, on_delete=models.CASCADE, related_name='samples', related_query_name='sample')
    collection_date = models.DateField()
    assembly = models.CharField(max_length=2555, null=True, editable=False)
    rast_folder = models.CharField(max_length=2555, null=True, editable=False)
    rgi_results = models.CharField(max_length=2555, null=True, editable=False)
    virulence_finder_results = models.CharField(max_length=2555, null=True, editable=False)

    def __str__(self):
        return self.identifier


class Sequence(models.Model):
    sample = models.OneToOneField(Sample,  on_delete=models.CASCADE)
    identifier = models.CharField(max_length=255, primary_key=True)
    sequence_date = models.DateField()
    sequence_file_pair1 = models.FileField(upload_to=sequence_directory_path, null=True, blank=True,
                                           validators=[fq_validate_file_extension])
    sequence_file_pair2 = models.FileField(upload_to=sequence_directory_path, null=True, blank=True,
                                           validators=[fq_validate_file_extension])
    assembly_file = models.FileField(upload_to=sequence_directory_path, null=True, validators=[fa_validate_file_extension], blank=True)

    def __str__(self):
        return '{0} ({1})'.format(self.identifier, self.sample.identifier)

    def run_pipeline(self):
        if not self.sample.component.filter(task__status='STARTED'):
            if self.sequence_file_pair1 and self.sequence_file_pair2:
                run_component.apply_async((self.sample.pk, 'ASSEMBLY'), link=group(
                    run_component.signature((self.sample.pk, 'ANNOTATION'), immutable=True),
                    run_component.signature((self.sample.pk, 'RESISTANCE_ANALYSIS'), immutable=True)
                ))
            elif self.assembly_file:
                sample = self.sample
                sample.assembly = self.assembly_file.path
                self.sample.save()
                tasks = group([run_component.signature((self.sample.pk, 'ANNOTATION'), immutable=True),
                               run_component.signature((self.sample.pk, 'RESISTANCE_ANALYSIS'), immutable=True),
                               run_component.signature((self.sample.pk, 'VIRULENCE_ANALYSIS'), immutable=True)
                               ])
                tasks.apply_async()

        else:
            raise Exception('Another pipeline is already running')

    def save(self, **kwargs):
        item = super(Sequence, self).save(**kwargs)
        self.run_pipeline()
        return item


@receiver(models.signals.post_delete, sender=Species)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.sequence_file:
        if os.path.isfile(instance.sequence_file.path):
            os.remove(instance.sequence_file.path)


@receiver(models.signals.post_delete, sender=Sequence)
def auto_delete_file_on_delete2(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.sequence_file_pair1:
        if os.path.isfile(instance.sequence_file_pair1.path):
            os.remove(instance.sequence_file_pair1.path)
    if instance.sequence_file_pair2:
        if os.path.isfile(instance.sequence_file_pair2.path):
            os.remove(instance.sequence_file_pair2.path)


@receiver(models.signals.pre_save, sender=Species)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `Sequence` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = Sequence.objects.get(pk=instance.pk).sequence_file
    except Sequence.DoesNotExist:
        return False

    new_file = instance.sequence_file
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
