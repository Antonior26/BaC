import os

from bac_tasks.pipelines.base import pipeline_step, JobFailedException


def run_virulence_analysis_pipeline(db_path, name, assembly, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    out = os.path.join(output_dir, name + '.json')
    pipeline_step('python /app/virulencefinder.py', '-i', assembly, '-o', out, '-p', db_path)
    return out