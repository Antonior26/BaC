import os

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.dispatch import receiver
from django_celery_results.models import TaskResult
from django.conf import settings
from Isolates.models import Sequence, Sample
from bac_tasks.pipelines.annotation import run_annotation_pipeline
from bac_tasks.pipelines.assembly import run_assembly_pipeline
from bac_tasks.pipelines.resistance_analysis import run_resistance_pipeline
from bac_tasks.pipelines.virulence_analysis import run_virulence_analysis_pipeline


def get_result_path(instance):
    return '{0}/{1}/{2}/{3}/{4}'.format(settings.PIPELINE_RESULTS_URI, instance.sample.isolate.identifier,
                                        instance.sample.identifier, instance.component_type, instance.id
                                        )


class ComponentTask(models.Model):
    COMPONENT_TYPES = (
        ('QC', 'QC'),
        ('ASSEMBLY', 'ASSEMBLY'),
        ('ALIGNMENT', 'ALIGNMENT'),
        ('VARIANT_CALLING', 'VARIANT_CALLING'),
        ('ANNOTATION', 'ANNOTATION'),
        ('COVERAGE', 'COVERAGE'),
        ('RESISTANCE_ANALYSIS', 'RESISTANCE_ANALYSIS'),
        ('VIRULENCE_ANALYSIS', 'VIRULENCE_ANALYSIS'),
    )

    component_type = models.CharField(choices=COMPONENT_TYPES, editable=False, max_length=250)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    last_update_date = models.DateTimeField(auto_now=True, editable=False)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, editable=False, related_name='component')
    result_folder = models.FilePathField(editable=False, null=True)
    task = models.ForeignKey(TaskResult, on_delete=models.CASCADE, default=None, null=True)
    seconds = models.IntegerField(default=None, null=True, editable=False)
    additional_parameters = JSONField(default={}, editable=False)

    class Meta:
        ordering = ['last_update_date']

    def get_command(self):
        if self.component_type == 'ASSEMBLY':
            return self.get_assembly_command()
        elif self.component_type == 'ANNOTATION':
            return self.get_annotation_command()
        elif self.component_type == 'RESISTANCE_ANALYSIS':
            return self.get_resistance_analysis_command()
        elif self.component_type == 'VIRULENCE_ANALYSIS':
            return self.get_virulence_analysis_command()
        else:
            raise NotImplementedError

    def get_assembly_command(self):
        params = settings.ASSEMBLY_PATHS
        params.update({
            'name': self.sample.identifier,
            'read1': self.sample.sequence.sequence_file_pair1.path,
            'read2': self.sample.sequence.sequence_file_pair2.path,
            'output_dir': self.result_folder
        })
        params.update(self.additional_parameters)
        return run_assembly_pipeline, params

    def get_annotation_command(self):
        params = settings.ANNOTATION_PATHS
        params.update({
            'name': self.sample.identifier,
            'assembly': self.sample.assembly,
            'sp': self.sample.isolate.species.name,
            'output_dir': self.result_folder
        })
        params.update(self.additional_parameters)
        return run_annotation_pipeline, params

    def get_resistance_analysis_command(self):
        params = settings.RGI_PATHS
        params.update({
            'assembly': self.sample.assembly,
            'output_dir': self.result_folder
        })
        params.update(self.additional_parameters)
        return run_resistance_pipeline, params

    def get_virulence_analysis_command(self):
        params = {
            'db_path': '/databases/virulencefinder_db/',
            'assembly': self.sample.assembly,
            'output_dir': self.result_folder
        }
        params.update(self.additional_parameters)
        return run_virulence_analysis_pipeline, params


@receiver(models.signals.post_save, sender=ComponentTask)
def auto_populate_result_folder(sender, instance, **kwargs):
    """
    Update the instance with
    """
    path = get_result_path(instance)
    os.makedirs(path, exist_ok=True)
    ComponentTask.objects.filter(id=instance.id).update(result_folder=get_result_path(instance))
