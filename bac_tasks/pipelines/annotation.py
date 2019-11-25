import json
import os

from django.conf import settings

from bac_tasks.pipelines.base import JobFailedException, PipelineComponent


class Annotation(PipelineComponent):
    _name = 'ANNOTATION'
    _workflow = {
        "stages":
            [
             {"name": "call_features_CDS_glimmer3",
              "glimmer3_parameters": {
                  "min_training_len": "2000"
              }},
             {"name": "annotate_proteins_similarity",
              "similarity_parameters": {
                  "annotate_hypothetical_only": "1"
              }},
             {"name": "resolve_overlapping_features",
              "resolve_overlapping_features_parameters": {}
              }
             ]
    }

    def _run(self):
        name = self.sample.identifier
        assembly = self.sample.assembly
        output_dir = self.result_folder
        sp = self.sample.isolate.species.name
        rast_create_genome = settings.ANNOTATION_PATHS['rast_create_genome']
        rast_process_genome = settings.ANNOTATION_PATHS['rast_process_genome']
        rast_export_genome = settings.ANNOTATION_PATHS['rast_export_genome']
        os.makedirs(output_dir, exist_ok=True)
        output_dir_exports = os.path.join(output_dir, 'exports')
        os.makedirs(output_dir_exports, exist_ok=True)
        workflow = os.path.join(output_dir, name + '.workflow')
        fdw = open(workflow, 'w')
        json.dump(self._workflow, fdw)
        fdw.close()
        gto = os.path.join(output_dir, name + '.gto')
        gto2 = os.path.join(output_dir, name + '.gto2')
        genebank = os.path.join(output_dir_exports, name + '.gbk')
        gff = os.path.join(output_dir_exports, name + '.gff')
        embl = os.path.join(output_dir_exports, name + '.embl')
        rna_fasta = os.path.join(output_dir_exports, name + '.rna.fasta')
        cds_fasta = os.path.join(output_dir_exports, name + '.cds.fasta')
        protein_fasta = os.path.join(output_dir_exports, name + '.proteins.fasta')

        self.pipeline_step(rast_create_genome, '-o', gto, '--contig', assembly, '--genetic-code', '11', '--genome-id',
                           name, '--domain', 'Bacteria', '--scientific-name', sp)
        self.pipeline_step(rast_process_genome, '-o', gto2, '-i', gto, '--workflow', workflow)

        self.pipeline_step(rast_export_genome, 'gff', '-i', gto2, '-o', gff)
        self.pipeline_step(rast_export_genome, 'protein_fasta', '-i', gto2, '-o', protein_fasta)
        self.pipeline_step(rast_export_genome, 'feature_dna', '--feature-type', 'rna', '-i', gto2, '-o', rna_fasta)
        self.pipeline_step(rast_export_genome, 'feature_dna', '--feature-type', 'CDS', '-i', gto2, '-o', cds_fasta)
        return self._results

    def post_run(self):
        if self._results is None:
            JobFailedException('Please execute job first using execute method')
        self.sample.rast_folder = self._results
        self.sample.save()

