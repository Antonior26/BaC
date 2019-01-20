import json
import random
import calendar
import csv

from app.Database import Database
from django.db.models import Count
from ete3 import NCBITaxa
import factory

from Isolates.models import Species, Patient, Isolate, AroGene, AroCategory, Sample, Result, Sequence


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'Isolates.AroGeneMatch'  # Equivalent to ``model = myapp.models.User``


def randomdate(year, month=None):
    if month is None:
        month = random.randint(1, 12)
    dates = calendar.Calendar().itermonthdates(year, month)
    return random.choice([date for date in dates if date.month == month])


def patient_loader(number=3000):
    for i in range(0, number):
        Patient.objects.create(identifier='PID_' + str(i))


def isolate_loader(number=5000):
    query_set_all_species = Species.objects.all()
    query_set_all_patients = Patient.objects.all()
    culture_type = ['Blood Agar', 'Eosin methylene blue', 'Granada medium', 'MacConkey agar']
    tissue_origin = ['blood', 'respiratory tract', 'urine', 'sputum']
    for i in range(0, number):
        species = query_set_all_species[
            random.randint(0, query_set_all_species.aggregate(count=Count('id'))['count'] - 1)]
        patient = query_set_all_patients[
            random.randint(0, query_set_all_patients.aggregate(count=Count('pk'))['count'] - 1)]
        Isolate.objects.create(identifier='IID_' + str(i), species=species, patient=patient,
                               culture_type=random.choice(culture_type),
                               tissue_origin=random.choice(tissue_origin), collection_date=randomdate(2017)
                               )


def sample_loader():
    for i, isolate in enumerate(Isolate.objects.all()):
        Sample.objects.create(identifier='SID_' + str(i), isolate=isolate, collection_date=randomdate(
            2017, month=(int(isolate.collection_date.month) + 1) if isolate.collection_date.month < 12 else 12)
                              )


def result_loader():
    g = json.load(open('/home/aruedamartin/res-test/test.json'))
    for sample in Sample.objects.all():
        Result.from_rgi_result_randomize(sample=sample, all_hits=g)


def create_aro_db():
    g = json.load(open('/home/aruedamartin/PycharmAntonio/BaC/reference/localDB/VFDB.json'))
    cat = set()
    for i in g:
        if i not in ['_version', '_comment', '_timestamp']:
            categories = g[i].pop('ARO_category')
            creation = {key.lower(): g[i][key] for key in g[i] if key not in ['model_param', 'model_sequences']}
            print(creation.keys())
            aro_gene = AroGene.objects.create(**creation)
            for c in categories:
                creation_categories = {key.lower(): categories[c][key] for key in categories[c]}
                print(creation_categories)
                category = AroCategory.objects.get_or_create(
                    category_aro_accession=creation_categories['category_aro_accession'],
                    defaults=creation_categories
                )
                aro_gene.aro_category.add(category[0])


def get_category_description(aline):
    return aline[3]


def get_category_name(aline):
    return aline[1] if aline[1] != "" else aline[0]


class FastaRecord(object):
    def __init__(self, id, seq):
        self.seq_id = id.split(' ')[0]
        self.name = id.split(' ')[1].replace('(', '').replace(')', '')
        self.protein_description = ' '.join(id.split(' ')[2:]).split('[')[0]
        id_identifiers = ' '.join(id.split(' ')[3:])
        self.category = id_identifiers.split('[')[1].split(' (')[0]
        self.category_id = id_identifiers.split('[')[1].split(' (')[1].split(')')[0]
        self.tax_id = id_identifiers.split('[')[2].split(' ')[-1].replace(']', '')
        self.tax_name = ' '.join(id_identifiers.split('[')[2].split(' ')[:-1])
        self.seq = seq


def create_vfdb_record(fasta_record, db_records, id):
    model_id = str(id)
    model_name = fasta_record.name
    model_type = 'protein homolog model'
    model_type_id = '40292'
    model_description = "The protein homolog model is an AMR detection model. Protein homolog models detect a protein " \
                        "sequence based on its similarity to a curated reference sequence. A protein homolog model " \
                        "has only one parameter: a curated BLASTP bitscore cutoff for determining the strength of a " \
                        "match. Protein homolog model matches to reference sequences are categorized on three " \
                        "criteria: \"perfect\", \"strict\" and \"loose\". A perfect match is 100% identical to the " \
                        "reference sequence along its entire length; a strict match is not identical but the bitscore " \
                        "of the matched sequence is greater than the curated BLASTP bitscore cutoff. Loose matches " \
                        "are other sequences with a match bitscore less than the curated BLASTP bitscore. "

    model_param = {"blastp_bit_score": {"param_type": "BLASTP bit-score",
                                        "param_description": "A score is a numerical value that describes the overall "
                                                             "quality of an alignment with higher numbers correspond "
                                                             "to higher similarity. The bit-score (S) is determined by "
                                                             "the following formula: S = (\u03bb \u00d7 S \u2212 "
                                                             "lnK)\/ ln2 where \u03bb is the Gumble distribution "
                                                             "constant, S is the raw alignment score, and K is a "
                                                             "constant associated with the scoring matrix. Many AMR "
                                                             "detection models use this parameter, including the "
                                                             "protein homolog and protein variant models. The BLASTP "
                                                             "bit-score parameter is a curated value determined from "
                                                             "BLASTP analysis of the canonical reference sequence of a "
                                                             "specific AMR-associated protein against the database of "
                                                             "CARD reference sequence. This value establishes a "
                                                             "threshold for computational prediction of a specific "
                                                             "protein amongst a batch of submitted sequences.",
                                        "param_type_id": "40725", "param_value": "575"}}

    ARO_accession = fasta_record.name
    ARO_name = fasta_record.name
    ARO_description = fasta_record.protein_description
    ARO_category = {
        fasta_record.category: {
            "category_aro_accession": fasta_record.category_id,
            "category_aro_cvterm_id": fasta_record.category_id,
            "category_aro_name": get_category_name(db_records[fasta_record.category]),
            "category_aro_description": get_category_description(db_records[fasta_record.category]),
            "category_aro_class_name": "Virulence Factors"
        }}
    model_sequences = {
        "sequence": {
            str(id): {
                "protein_sequence": {
                    "accession": fasta_record.seq_id,
                    "sequence": fasta_record.seq
                },
                "NCBI_taxonomy": {
                    "NCBI_taxonomy_cvterm_id": fasta_record.tax_id,
                    "NCBI_taxonomy_name": fasta_record.tax_name,
                    "NCBI_taxonomy_id": fasta_record.tax_id
                }

            }}}

    results = {

                'model_id': model_id,
                'model_name': model_name,
                'model_type': model_type,
                'model_type_id': model_type_id,
                'model_description': model_description,
                'model_param': model_param,
                'ARO_accession': ARO_accession,
                'ARO_name': ARO_name,
                'ARO_description': ARO_description,
                'ARO_category': ARO_category,
                'model_sequences': model_sequences
    }

    return results


def read_vf_records(ifile='/home/aruedamartin/PycharmAntonio/BaC/reference/VFDBlocal/VFs.csv'):
    records = {}

    with open(ifile) as fd:
        reader = csv.reader(fd, delimiter='\t', quotechar='"')
        for aline in reader:
            records[aline[0]] = aline
    return records


def read_fasta_records(ifile='/home/aruedamartin/PycharmAntonio/BaC/reference/VFDBlocal/VFDB.fa'):
    records = []
    with open(ifile) as fd:
        new_record = None
        for line in fd:
            if line.startswith('>'):
                if new_record:
                    records.append(FastaRecord(id=new_record[0], seq=new_record[1]))
                new_record = [line.rstrip('\n'), '']
            else:
                new_record[1] += line.rstrip('\n')
        if new_record:
            records.append(FastaRecord(id=new_record[0], seq=new_record[1]))

    return records

def create_json():
    db = read_vf_records()
    fasta_records = read_fasta_records()
    all_records = {}
    for e, fr in enumerate(fasta_records):
        if fr.category in db:
            all_records[str(e)] = create_vfdb_record(fr, db, e)
        else:
            print(fr.category)

    with open('/home/aruedamartin/PycharmAntonio/BaC/reference/VFDBlocal/VFDB.json', 'w') as vfdb:
        json.dump(all_records, vfdb, indent=True)


db_obj = Database('/home/aruedamartin/PycharmAntonio/BaC/reference/VFDBlocal/VFDB.json')
db_obj.build_databases()