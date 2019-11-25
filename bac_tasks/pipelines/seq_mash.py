import os

from django.conf import settings

from Isolates.models import Species
from bac_tasks.pipelines.base import PipelineComponent, JobFailedException

class SeqMash(PipelineComponent):
    _name = 'SeqMash'

    def parse_results(self):
        content = {}
        with open(self._results) as result_file:
            header = result_file.readline().replace('\n', '').split('\t')
            data = result_file.readline().replace('\n', '').split('\t')

        for h, d in zip(header, data):
            content[h] = d

        return content

    def _run(self):
        os.makedirs(self.result_folder, exist_ok=True)
        output = os.path.join(self.result_folder, 'matches.tsv')
        path = settings.REFSEQ_MASHER_PATHS['refseq_masher_path']

        if self.sample.assembly:
            self.pipeline_step(path, 'matches', self.sample.assembly, '-o', output, '--output-type', 'tab')
        else:
            self.pipeline_step(path, 'matches', self.sample.sequence.sequence_file_pair1,
                               self.sample.sequence.sequence_file_pair2,
                               '-o', output, '--output-type', 'tab')

        return output

    def post_run(self):
        if self._results is None:
            JobFailedException('Please execute job first using execute method')

        result_content = self.parse_results()
        species = Species.objects.create(name=result_content['taxonomic_species'],
                                         genus=result_content['taxonomic_genus'],
                                         family=result_content['taxonomic_family'],
                                         order=result_content['taxonomic_order'],
                                         klass=result_content['taxonomic_class'],
                                         phylum=result_content['taxonomic_phylum'],
                                         kingdom=result_content['taxonomic_superkingdom']
                                         )
        isolate = self.sample.isolate
        isolate.species = species
        isolate.save()
