import json
import os

from .base import pipeline_step, JobFailedException

WORKFLOW = {
    "stages":
        [{"name": "call_features_rRNA_SEED"},
         {"name": "call_features_tRNA_trnascan"},
         {"name": "call_features_repeat_region_SEED",
          "repeat_region_SEED_parameters": {
              "min_identity": "95",
              "min_length": "100"
          }},
         {"name": "call_pyrrolysoproteins"},
         {"name": "call_selenoproteins"},
         {"name": "call_features_insertion_sequences"},
         {"name": "call_features_crispr"},
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

# TODO: {"name": "call_features_prophage_phispy"} has been removed due to failures, investigate and add again

def run_annotation_pipeline(rast_create_genome, rast_process_genome, rast_export_genome, name, assembly, output_dir, sp):
    os.makedirs(output_dir, exist_ok=True)
    output_dir_exports = os.path.join(output_dir, 'exports')
    os.makedirs(output_dir_exports, exist_ok=True)
    workflow = os.path.join(output_dir, name + '.workflow')
    fdw = open(workflow, 'w')
    json.dump(WORKFLOW, fdw)
    fdw.close()
    gto = os.path.join(output_dir, name + '.gto')
    gto2 = os.path.join(output_dir, name + '.gto2')
    genebank = os.path.join(output_dir_exports, name + '.gbk')
    gff = os.path.join(output_dir_exports, name + '.gff')
    embl = os.path.join(output_dir_exports, name + '.embl')
    rna_fasta = os.path.join(output_dir_exports, name + '.rna.fasta')
    cds_fasta = os.path.join(output_dir_exports, name + '.cds.fasta')
    protein_fasta = os.path.join(output_dir_exports, name + '.proteins.fasta')

    pipeline_step(rast_create_genome, '-o', gto, '--contig', assembly, '--genetic-code', '11', '--genome-id', name,
                  '--domain', 'Bacteria', '--scientific-name', sp)
    pipeline_step(rast_process_genome, '-o', gto2, '-i', gto, '--workflow', workflow)

    pipeline_step(rast_export_genome, 'genbank', '-i', gto2, '-o', genebank)
    pipeline_step(rast_export_genome, 'gff', '-i', gto2, '-o', gff)
    pipeline_step(rast_export_genome, 'embl', '-i', gto2, '-o', embl)
    pipeline_step(rast_export_genome, 'protein_fasta', '-i', gto2, '-o', protein_fasta)
    pipeline_step(rast_export_genome, 'feature_dna', '--feature-type', 'rna', '-i', gto2, '-o', rna_fasta)
    pipeline_step(rast_export_genome, 'feature_dna', '--feature-type', 'CDS', '-i', gto2, '-o', cds_fasta)

    return output_dir_exports
