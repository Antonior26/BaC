import os

from bac_tasks.pipelines.base import pipeline_step, JobFailedException


def run_resistance_pipeline(rgi_path, db_path, name, assembly, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    out = os.path.join(output_dir, 'data.json')
    pipeline_step(rgi_path, 'main', '--local', '-i', assembly, '-o', output_dir, cwd=db_path)
    return out
