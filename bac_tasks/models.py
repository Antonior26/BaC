import os

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.dispatch import receiver
from django_celery_results.models import TaskResult
from django.conf import settings
from Isolates.models import Sample
from bac_tasks.pipelines import COMPONENT_TYPES, Assembly, Annotation, Resistance, Virulence, SeqMash
from bac_tasks.pipelines.resfinder_analysis import Resfinder


def get_result_path(instance):
    return '{0}/{1}/{2}/{3}/{4}'.format(settings.PIPELINE_RESULTS_URI, instance.sample.isolate.identifier,
                                        instance.sample.identifier, instance.component_type, instance.id
                                        )


class ComponentTask(models.Model):
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

    def get_component(self):
        if self.component_type == 'ASSEMBLY':
            component = Assembly
        elif self.component_type == 'ANNOTATION':
            component = Annotation
        elif self.component_type == 'RESISTANCE_ANALYSIS':
            component = Resistance
        elif self.component_type == 'VIRULENCE_ANALYSIS':
            component = Virulence
        elif self.component_type == 'RESFINDER_ANALYSIS':
            component = Resfinder
        elif self.component_type == 'REFSEQ_MASHER':
            component = SeqMash
        else:
            raise NotImplementedError
        return component(self.sample, self.result_folder)


@receiver(models.signals.post_save, sender=ComponentTask)
def auto_populate_result_folder(sender, instance, **kwargs):
    """
    Update the instance with
    """
    path = get_result_path(instance)
    os.makedirs(path, exist_ok=True)
    ComponentTask.objects.filter(id=instance.id).update(result_folder=get_result_path(instance))
