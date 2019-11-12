import os

from bac_tasks.pipelines.base import pipeline_step, JobFailedException


def run_virulence_analysis_pipeline(db_path, assembly, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    out = os.path.join(output_dir, 'data.json')
    pipeline_step('/opt/virulencefinder/virulencefinder.py', '-i', assembly, '-o', output_dir, '-p', db_path,
                  '--threshold', '0.8')
    return out
