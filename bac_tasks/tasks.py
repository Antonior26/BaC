# Create your tasks here
import json
import logging
import time

from celery import shared_task, states
from django.apps import apps
from django_celery_results.models import TaskResult
from ete3 import NCBITaxa

logging.basicConfig(level=logging.INFO)


@shared_task(autoretry_for=(Exception,), default_retry_delay=10, max_retries=1)
def run_component(sample_id, component_type):
    component_task_model = apps.get_model('bac_tasks', 'ComponentTask')
    sample_model = apps.get_model('Isolates', 'Sample')
    logging.info(component_task_model)
    sample = sample_model.objects.get(pk=sample_id)
    logging.info(sample.pk)
    component_task = component_task_model.objects.create(sample=sample, component_type=component_type)
    component_task = component_task_model.objects.get(pk=component_task.pk)
    task_id = run_component.request.id
    logging.info("Starting task with id '{}'".format(task_id))
    # saves the task in pending status

    task_result, created = TaskResult.objects.get_or_create(task_id=task_id, defaults={
        'status': states.STARTED
    })
    # associates the task to the sample ingestion entity
    component_task.task = task_result
    component_task.save()
    start_time = time.time()
    try:
        component = component_task.get_component()
        component.execute()
        component.post_run()
        seconds = time.time() - start_time
        logging.info("Task succeeded in {} seconds!".format(seconds))
        component_task.seconds = int(seconds)
        component_task.save(update_fields=["seconds"])

    except Exception as ex:
        seconds = time.time() - start_time
        component_task.seconds = int(seconds)
        component_task.save(update_fields=["seconds"])
        logging.error("Task failed: {}".format(str(ex)))
        raise ex


@shared_task()
def run_load_taxa_data():
    reference_species = apps.get_model('Isolates', 'ReferenceSpecies')
    if reference_species.objects.filter().count() == 0:
        ncbi = NCBITaxa()
        descendants = ncbi.get_descendant_taxa('Bacteria')
        ranks = ncbi.get_rank(descendants)
        ranks = {k: v for k, v in ranks.items() if v == 'species'}
        for species in ranks:
            logging.info(species)
            lineage = ncbi.get_lineage(species)
            lineage_ranks = ncbi.get_rank(lineage)
            lineage_names = ncbi.get_taxid_translator(lineage)
            species_name, klass, kingdom, genus, phylum, order, family = [None, None, None, None, None, None, None]
            for l in lineage:
                if lineage_ranks[l] in 'superkingdom':
                    kingdom = lineage_names[l]
                elif lineage_ranks[l] == 'family':
                    family = lineage_names[l]
                elif lineage_ranks[l] in 'genus':
                    genus = lineage_names[l]
                elif lineage_ranks[l] in 'phylum':
                    phylum = lineage_names[l]
                elif lineage_ranks[l] in 'species':
                    species_name = lineage_names[l]
                elif lineage_ranks[l] in 'class':
                    klass = lineage_names[l]
                elif lineage_ranks[l] in 'order':
                    order = lineage_names[l]
            if species_name and klass and kingdom and genus and phylum and order and family:
                logging.info('{}: {} - {} - {} - {} - {} - {}'.format(species_name, klass, kingdom, genus,
                                                                      phylum, order, family))
                try:
                    sp = reference_species.objects.update_or_create(name=species_name,
                                                                    defaults=dict(
                                                                        klass=klass,
                                                                        kingdom=kingdom,
                                                                        genus=genus,
                                                                        phylum=phylum,
                                                                        order=order,
                                                                        family=family))
                    logging.info('{} created'.format(sp[0].name))
                except Exception as e:
                    logging.error(e)
            else:
                logging.error('{}: {} - {} - {} - {} - {} - {}'.format(species_name, klass, kingdom, genus,
                                                                      phylum, order, family))

    else:
        logging.warning('Data is already loaded nothing else to do here.')

