import os
import subprocess


class JobFailedException(Exception):
    pass


def pipeline_step(command, *args, cwd=None):
    if args:
        command = [command] + list(args)
        print(' '.join(command))
    try:
        env = os.environ.copy()
        env['PATH'] = '/home/aruedamartin/miniconda3/envs/BaC/bin:' + env['PATH']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env)
        output, error = process.communicate()
        if error:
            raise JobFailedException(error)
    except Exception as e:
        raise JobFailedException(str(e))
    return output
