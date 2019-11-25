import os
import subprocess


class JobFailedException(Exception):
    pass


class PipelineComponent:
    _name = None
    _results = None

    def __init__(self, sample, result_folder):
        self.result_folder = result_folder
        self.sample = sample

    @property
    def name(self):
        return self._name

    def _run(self, *args, **kwargs):
        raise NotImplementedError()

    def execute(self, *args, **kwargs):
        self._results = self._run(*args, **kwargs)

    def pre_run(self):
        return None

    def post_run(self):
        return None

    @staticmethod
    def pipeline_step(command, *args, **kwargs):
        cwd = kwargs.get('cwd', None)

        if args:
            command = [command] + list(args)
            print(' '.join(command))
        try:
            env = os.environ.copy()
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env)
            output, error = process.communicate()
            if error:
                raise JobFailedException(error)
        except Exception as e:
            raise JobFailedException(str(e))
        return output


