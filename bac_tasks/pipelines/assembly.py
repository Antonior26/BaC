import os

from django.conf import settings

from .base import PipelineComponent, JobFailedException


class Assembly(PipelineComponent):
    def _run(self):

        spades_path = settings.ASSEMBLY_PATHS['spades_path']
        os.makedirs(self.result_folder, exist_ok=True)
        self.pipeline_step(spades_path,
                           '--threads', settings.ASSEMBLY_THREADS,
                           '-1', self.sample.sequence.sequence_file_pair1.path,
                           '-2', self.sample.sequence.sequence_file_pair2.path,
                           '-o', self.result_folder,
                           '--tmp-dir', os.path.join(settings.TMP, self.sample.identifier),
                           '--mismatch-correction',
                           '--careful'
                           )

        final_assembly = os.path.join(self.result_folder, 'scaffolds.fasta')
        return final_assembly

    def post_run(self):
        if self._results is None:
            JobFailedException('Please execute job first using execute method')
        self.sample.assembly = self._results
        self.sample.save()
