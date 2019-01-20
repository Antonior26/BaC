import os

from .base import pipeline_step, JobFailedException


def count_assembly(ifile):
    with open(ifile) as fd:
        bases_len = len(''.join([line.rstrip('\n') for line in fd if not line.startswith('\n')]))
    return bases_len


def evaluated_qc(velvet_path, spades_path):
    velvet_assembly = os.path.join(velvet_path, 'contigs.fa')
    spades_assembly = os.path.join(spades_path, 'scaffolds.fasta')

    velvet_count = count_assembly(velvet_assembly)
    spades_count = count_assembly(spades_assembly)
    if velvet_count > spades_count:
        return 'velvet', velvet_assembly
    return 'spades', spades_assembly


def run_assembly_pipeline(name, spades_path, velveth_path, velvetg_path, qc_path, read1, read2, output_dir,
                          do_error_correction=True, fast=True, tmp='/tmp/'):
    if do_error_correction and not fast:
        output_dir_error_correction = os.path.join(output_dir, 'error_correction')
        corrected_read1 = os.path.join(output_dir_error_correction, 'corrected',
                                       os.path.basename(read1).replace('.gz', '.00.0_0.cor.fastq.gz'))
        corrected_read2 = os.path.join(output_dir_error_correction, 'corrected',
                                       os.path.basename(read2).replace('.gz', '.00.0_0.cor.fastq.gz'))
        os.makedirs(output_dir_error_correction, exist_ok=True)
        pipeline_step(spades_path, '--only-error-correction', '-1', read1, '-2', read2, '-o',
                      output_dir_error_correction, '--tmp-dir', os.path.join(tmp, name))
    else:
        corrected_read2 = read2
        corrected_read1 = read1

    output_dir_spades = os.path.join(output_dir, 'spades')
    os.makedirs(output_dir_spades, exist_ok=True)
    output_dir_final_assembly = os.path.join(output_dir, 'assmebly')
    os.makedirs(output_dir_final_assembly, exist_ok=True)
    pipeline_step(spades_path, '--only-assembler', '-1', corrected_read1, '-2', corrected_read2, '-k', '21,33',
                  '-o', output_dir_spades, '--tmp-dir', os.path.join(tmp, name))

    final_assembly = os.path.join(output_dir_final_assembly, name + '.fasta')

    if not fast:
        output_dir_velvet = os.path.join(output_dir, 'velvet')
        os.makedirs(output_dir_velvet, exist_ok=True)
        output_dir_qc = os.path.join(output_dir, 'qc')
        os.makedirs(output_dir_qc, exist_ok=True)
        pipeline_step(velveth_path, output_dir_velvet, '31', '-shortPaired', '-fastq.gz', corrected_read1,
                      '-shortPaired2', '-fastq.gz', corrected_read2)
        pipeline_step(velvetg_path, output_dir_velvet)
        selected_tool, selected_assembly = evaluated_qc(output_dir_velvet, output_dir_spades)

    else:
        selected_assembly = os.path.join(output_dir_spades, 'scaffolds.fasta')

    pipeline_step('cp', selected_assembly, final_assembly)
    return final_assembly
