import json
import os

from django.apps import apps
from django.conf import settings

from bac_tasks.pipelines.base import PipelineComponent, JobFailedException


class Resistance(PipelineComponent):
    _name = 'RESISTANCE_ANALYSIS'

    def _run(self):
        rgi_path = settings.RGI_PATHS['rgi_path']
        db_path = settings.RGI_PATHS['db_path']
        os.makedirs(self.result_folder, exist_ok=True)
        out = os.path.join(self.result_folder, 'data.json')
        self.pipeline_step(rgi_path, 'main', '--local', '-i', self.sample.assembly, '-o', out, cwd=db_path)
        return out

    def post_run(self):
        result_model = apps.get_model('Isolates', 'Result')
        if self._results is None:
            JobFailedException('Please execute job first using execute method')
        self.sample.rgi_results = self._results
        self.sample.save()
        result_model.objects.filter(sample=self.sample, type=self._name).delete()
        g = json.load(open(self.sample.rgi_results))
        result_model.from_rgi_result(g, self.sample, (self.sample.sequence,))
