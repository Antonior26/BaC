import logging

from bac_tasks.tasks import run_load_taxa_data

logging.basicConfig(level=logging.INFO)


def run():
    run_load_taxa_data.apply_async()
