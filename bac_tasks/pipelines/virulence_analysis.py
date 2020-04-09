import json
import os

from django.apps import apps
from django.conf import settings

from bac_tasks.pipelines.base import PipelineComponent, JobFailedException


class Virulence(PipelineComponent):
    _name = 'VIRULENCE_ANALYSIS'

    def _run(self):
        virulence_finder = settings.VIRULENCE_FINDER_PATHS['virulence_finder']
        db_path = settings.VIRULENCE_FINDER_PATHS['db_path']
        os.makedirs(self.result_folder, exist_ok=True)
        out = os.path.join(self.result_folder, 'data.json')
        self.pipeline_step(virulence_finder, '-i', self.sample.assembly, '-o', self.result_folder, '-p', db_path,
                           '--threshold', '0.9')
        return out

    def post_run(self):
        result_model = apps.get_model('Isolates', 'Result')
        if self._results is None:
            JobFailedException('Please execute job first using execute method')
        self.sample.virulence_finder_results = self._results
        self.sample.save()
        result_model.objects.filter(sample=self.sample, type=self._name).delete()
        g = json.load(open(self.sample.virulence_finder_results))
        result_model.from_virulence_finder_result(g, self.sample, (self.sample.sequence, ))
