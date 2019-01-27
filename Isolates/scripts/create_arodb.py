import json
import logging
import os

from Isolates.models import AroGene, AroCategory

logging.basicConfig(level=logging.INFO)


def create_aro_db():
    g = json.load(open(os.path.join(os.getenv('BAC_DB_PATH'), 'localDB', 'card.json')))
    for i in g:
        if i not in ['_version', '_comment', '_timestamp']:
            categories = g[i].pop('ARO_category')
            creation = {key.lower(): g[i][key] for key in g[i] if key not in ['model_param', 'model_sequences']}
            aro_gene = AroGene.objects.create(**creation)
            for c in categories:
                creation_categories = {key.lower(): categories[c][key] for key in categories[c]}
                category = AroCategory.objects.get_or_create(
                    category_aro_accession=creation_categories['category_aro_accession'],
                    defaults=creation_categories
                )
                aro_gene.aro_category.add(category[0])


def run():
    if AroGene.objects.filter().count() == 0:
        create_aro_db()