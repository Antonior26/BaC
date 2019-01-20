import os
import random

from celery import group
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count
from django.dispatch import receiver
from django.urls import reverse

from bac_tasks.tasks import run_component


def sequence_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<sample>/<sequence_id>/<filename>
    return 'sequence_results/{0}/{1}/{2}'.format(instance.sample, instance.identifier, filename)

def sample_sequence_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<sample>/<sequence_id>/<filename>
    return 'reference_genomes/{0}/{1}'.format(instance.name, filename)

def fq_validate_file_extension(value):
    valid_extensions = ['.fq.gz', '.fastq.gz']
    if not value.name.endswith('.fastq.gz') and not value.name.endswith('.fq.gz'):
        raise ValidationError(u'Unsupported file extension. Supported File extensions: {}'.format(
            ','.join(valid_extensions)
        ))
def fa_validate_file_extension(value):
    valid_extensions = ['.fa', '.fasta']
    if not value.name.endswith('.fa') and not value.name.endswith('.fasta'):
        raise ValidationError(u'Unsupported file extension. Supported File extensions: {}'.format(
            ','.join(valid_extensions)
        ))


class RastResult(models.Model):
    contig = models.CharField(max_length=255, null=False)
    start = models.CharField(max_length=255, null=False)
    end = models.CharField(max_length=255, null=False)
    strand = models.CharField(max_length=255, null=False)
    type = models.CharField(max_length=255, null=False)
    id = models.CharField(max_length=255, null=False)
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True

    @classmethod
    def from_gff_line(cls, line):
        aline = line.replace('\n', '').split('\t')
        properties = {p.split('=')[0]: p.split('=')[1] for p in aline[8].split(';')}
        return cls(contig=aline[0], start=aline[3], end=aline[4], strand=aline[6], type=aline[2],
                   id=properties.get('ID'), name=properties.get('Name')
                   )


class ReferenceSpecies(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    genus = models.CharField(max_length=255, null=False, blank=False)
    family = models.CharField(max_length=255, null=False, blank=False)
    order = models.CharField(max_length=255, null=False, blank=False)
    klass = models.CharField(max_length=255, null=False, blank=False)
    phylum = models.CharField(max_length=255, null=False, blank=False)
    kingdom = models.CharField(max_length=255, null=False, blank=False)

    def copy_to_species(self):
        return Species.objects.update_or_create(name=self.name,
                                                defaults={
                                                    'genus': self.genus,
                                                    'family': self.family,
                                                    'order': self.order,
                                                    'klass': self.klass,
                                                    'phylum': self.phylum,
                                                    'kingdom': self.kingdom,
                                                })


class Species(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    genus = models.CharField(max_length=255, null=False, blank=False)
    family = models.CharField(max_length=255, null=False, blank=False)
    order = models.CharField(max_length=255, null=False, blank=False)
    klass = models.CharField(max_length=255, null=False, blank=False)
    phylum = models.CharField(max_length=255, null=False, blank=False)
    kingdom = models.CharField(max_length=255, null=False, blank=False)
    sequence_file = models.FileField(upload_to=sample_sequence_directory_path)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('isolate-list') + '?species={}'.format(self.pk)

    def create_from_ref(self, reference_species):
        """

        :type reference_species: ReferenceSpecies
        """
        return self.objects.update_or_create(name=reference_species.name,
                                             defaults={
                                                 'genus': reference_species.genus,
                                                 'family': reference_species.family,
                                                 'order': reference_species.order,
                                                 'klass': reference_species.klass,
                                                 'phylum': reference_species.phylum,
                                                 'kingdom': reference_species.kingdom,
                                             })[0]

    def __str__(self):
        return self.name


class OntologyTerm(models.Model):
    ontology = models.CharField(max_length=255)
    term_id = models.CharField(max_length=255, primary_key=True)
    label = models.CharField(max_length=255)
    description = models.CharField(max_length=2555)

    def __str__(self):
        return '{} ({})'.format(self.label or self.term_id, self.ontology)

    def get_absolute_url(self):
        return 'https://www.ebi.ac.uk/ols/ontologies/{}/terms?iri=http://purl.obolibrary.org/obo/{}'.format(
            self.ontology.lower(), self.term_id.replace(':', '_')
        )


class AntibioticTest(models.Model):
    AMX = models.BooleanField(verbose_name='Amoxicillin(AMX)', default=False)
    AMC = models.BooleanField(verbose_name='Amoxicillin with clavulanic acid(AMC)', default=False)
    OX = models.BooleanField(verbose_name='Oxacillin(OX)', default=False)
    TIC = models.BooleanField(verbose_name='Ticarcillin(TIC)', default=False)
    TCC = models.BooleanField(verbose_name='Ticarcillin-clavulanic acid(TCC)', default=False)
    PIP = models.BooleanField(verbose_name='Piperacillin(PIP)', default=False)
    TZP = models.BooleanField(verbose_name='Piperacillin-tazobactam (TZP)', default=False)
    ATM = models.BooleanField(verbose_name='Aztreonam(ATM)', default=False)
    CF = models.BooleanField(verbose_name='Cefalotin(CF)', default=False)
    CXM = models.BooleanField(verbose_name='Cefuroxime(CXM)', default=False)
    FOX = models.BooleanField(verbose_name='Cefoxitin(FOX)', default=False)
    CTX = models.BooleanField(verbose_name='Cefotaxime(CTX)', default=False)
    CAZ = models.BooleanField(verbose_name='Ceftazidime(CAZ)', default=False)
    CRO = models.BooleanField(verbose_name='Ceftriaxone(CRO)', default=False)
    FEP = models.BooleanField(verbose_name='Cefepime(FEP)', default=False)
    K = models.BooleanField(verbose_name='Kanamycin(K)', default=False)
    GM = models.BooleanField(verbose_name='Gentamicin(GM)', default=False)
    TOB = models.BooleanField(verbose_name='Tobramycin(TOB)', default=False)
    NET = models.BooleanField(verbose_name='Netilmicin(NET)', default=False)
    AN = models.BooleanField(verbose_name='Amikacin(AN)', default=False)
    FOS = models.BooleanField(verbose_name='Fosfomycin(FOS)', default=False)
    RA = models.BooleanField(verbose_name='Rifampin(RA)', default=False)
    C = models.BooleanField(verbose_name='Chloramphenicol(C)', default=False)
    NA = models.BooleanField(verbose_name='Nalidixic acid(NA)', default=False)
    NOR = models.BooleanField(verbose_name='Norfloxacin(NOR)', default=False)
    PEF = models.BooleanField(verbose_name='Plefloxacin(PEF)', default=False)
    OFX = models.BooleanField(verbose_name='Ofloxacin(OFX)', default=False)
    CIP = models.BooleanField(verbose_name='Ciprofloxacin(CIP)', default=False)
    LEV = models.BooleanField(verbose_name='Levofloxacin(LEV)', default=False)
    L = models.BooleanField(verbose_name='Lincomycin(L)', default=False)
    E = models.BooleanField(verbose_name='Erythromycin(E)', default=False)
    CC = models.BooleanField(verbose_name='Clindamycin(CC)', default=False)
    SP = models.BooleanField(verbose_name='Spiramycin(SP)', default=False)
    PR = models.BooleanField(verbose_name='Pristinamycin(PR)', default=False)
    VA = models.BooleanField(verbose_name='Vancomycin(VA)', default=False)
    TEC = models.BooleanField(verbose_name='Teicoplanin(TEC)', default=False)
    SXT = models.BooleanField(verbose_name='Sulfamethoxazole with trimethoprim(SXT)', default=False)
    SSS = models.BooleanField(verbose_name='Triple sulfa(SSS)', default=False)
    TMP = models.BooleanField(verbose_name='Trimethoprim(TMP)', default=False)
    TE = models.BooleanField(verbose_name='Tetracycline(TE)', default=False)
    CS = models.BooleanField(verbose_name='Colistin(CS)', default=False)
    FA = models.BooleanField(verbose_name='Fusidic acid(FA)', default=False)
    LNZ = models.BooleanField(verbose_name='Linezolid(LNZ)', default=False)
    MNO = models.BooleanField(verbose_name='Minocycline(MNO)', default=False)
    FT = models.BooleanField(verbose_name='Nitrofurantoin(FT)', default=False)
    TEL = models.BooleanField(verbose_name='Telithromycin(TEL)', default=False)
    IPM = models.BooleanField(verbose_name='Imipenem(IPM)', default=False)


class Patient(models.Model):
    identifier = models.CharField(max_length=255, primary_key=True)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('isolate-list') + '?patient={}'.format(self.pk)

    def __str__(self):
        return str(self.identifier)


class HumanOntologyTerm(models.Model):
    ontology_term = models.ForeignKey(OntologyTerm, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='phenotype')


class Isolate(models.Model):
    identifier = models.CharField(max_length=255, primary_key=True)
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='species')
    collection_date = models.DateField()
    culture_type = models.CharField(max_length=255)
    tissue_origin = models.CharField(max_length=255)
    resistance = models.OneToOneField(AntibioticTest, related_name='resistances',
                                      on_delete=models.CASCADE, blank=True, null=True, editable=False)
    susceptibility = models.OneToOneField(AntibioticTest, related_name='susceptibilies',
                                          on_delete=models.CASCADE, blank=True, null=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    class Meta:
        ordering = ['collection_date']

    def get_samples_names(self):
        return [s.identifier for s in self.samples.all()]

    def get_absolute_url(self):
        return reverse('isolate-detail-view', kwargs={'pk': self.pk})

    def __str__(self):
        return self.identifier


class BacteriaOntologyTerm(models.Model):
    ontology_term = models.ForeignKey(OntologyTerm, on_delete=models.CASCADE)
    isolate = models.ForeignKey(Isolate, on_delete=models.CASCADE, related_name='phenotype')


class Sample(models.Model):
    identifier = models.CharField(max_length=255, primary_key=True)
    isolate = models.ForeignKey(Isolate, on_delete=models.CASCADE, related_name='samples', related_query_name='sample')
    collection_date = models.DateField()
    assembly = models.CharField(max_length=2555, null=True, editable=False)
    rast_folder = models.CharField(max_length=2555, null=True, editable=False )
    rgi_results = models.CharField(max_length=2555, null=True, editable=False)

    def __str__(self):
        return self.identifier


class Sequence(models.Model):
    sample = models.OneToOneField(Sample,  on_delete=models.CASCADE)
    identifier = models.CharField(max_length=255, primary_key=True)
    sequence_date = models.DateField()
    sequence_file_pair1 = models.FileField(upload_to=sequence_directory_path, null=True, blank=True,
                                           validators=[fq_validate_file_extension])
    sequence_file_pair2 = models.FileField(upload_to=sequence_directory_path, null=True, blank=True,
                                           validators=[fq_validate_file_extension])
    assembly_file = models.FileField(upload_to=sequence_directory_path, null=True, validators=[fa_validate_file_extension], blank=True)

    def __str__(self):
        return '{0} ({1})'.format(self.identifier, self.sample.identifier)

    def run_pipeline(self):
        if not self.sample.component.filter(task__status='STARTED'):
            if self.sequence_file_pair1 and self.sequence_file_pair2:
                run_component.apply_async((self.sample.pk, 'ASSEMBLY'), link=group(
                    run_component.signature((self.sample.pk, 'ANNOTATION'), immutable=True),
                    run_component.signature((self.sample.pk, 'RESISTANCE_ANALYSIS'), immutable=True)
                ))
            elif self.assembly_file:
                sample = self.sample
                sample.assembly = self.assembly_file.path
                self.sample.save()
                tasks = group([run_component.signature((self.sample.pk, 'ANNOTATION'), immutable=True),
                               run_component.signature((self.sample.pk, 'RESISTANCE_ANALYSIS'), immutable=True)
                               ])
                tasks.apply_async()

        else:
            raise Exception('Another pipeline is already running')

    def save(self, **kwargs):
        item = super(Sequence, self).save(**kwargs)
        self.run_pipeline()
        return item


class Result(models.Model):
    date = models.DateTimeField(auto_now=True, editable=False)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, editable=False)
    sequences = models.ManyToManyField(Sequence, editable=False)

    @classmethod
    def from_rgi_result(cls, all_hits, sample, sequences=()):
        result = cls.objects.create(sample=sample)
        for s in sequences:
            result.sequences.add(s)
        for contig_hits in all_hits:
            AroGeneMatch.from_rgi_result(all_hits[contig_hits], result)

    @classmethod
    def from_rgi_result_randomize(cls, all_hits, sample, sequences=()):
        result = cls.objects.create(sample=sample)
        for s in sequences:
            result.sequences.add(s)
        for contig_hits in all_hits:
            AroGeneMatch.from_rgi_result_randomize(all_hits[contig_hits], result)


class AroCategory(models.Model):
    CATEGORIES = (
        ('AMR Gene Family', 'AMR Gene Family'),
        ('Resistance Mechanism', 'Resistance Mechanism'),
        ('Efflux Regulator', 'Efflux Regulator'),
        ('Antibiotic', 'Antibiotic'),
        ('Adjuvant', 'Adjuvant'),
        ('Efflux Component', 'Efflux Component'),
        ('Drug Class', 'Drug Class'),
    )
    category_aro_accession = models.CharField(max_length=250, editable=False, unique=True)
    category_aro_cvterm_id = models.CharField(max_length=250, editable=False)
    category_aro_name = models.CharField(max_length=250, editable=False)
    category_aro_description = models.CharField(max_length=2500, editable=False)
    category_aro_class_name = models.CharField(max_length=250, editable=False, choices=CATEGORIES)

    def __str__(self):
        return self.category_aro_name


class AroGene(models.Model):
    model_id = models.CharField(max_length=250, editable=False, unique=True, primary_key=True)
    model_name = models.CharField(max_length=250, editable=False)
    model_type = models.CharField(max_length=250, editable=False)
    model_type_id = models.CharField(max_length=250, editable=False)
    model_description = models.CharField(max_length=2500, editable=False)
    aro_accession = models.CharField(max_length=250, editable=False)
    aro_id = models.CharField(max_length=250, editable=False)
    aro_name = models.CharField(max_length=2500, editable=False)
    aro_description = models.CharField(max_length=2500, editable=False)
    aro_category = models.ManyToManyField(AroCategory, related_name='aro_gene', editable=False)


class AroGeneMatch(models.Model):

    TYPE_MATCH = (('Loose', 'Loose'),
                  ('Perfect', 'Perfect'),
                  ('Strict', 'Strict')
                  )

    result = models.ForeignKey(Result, related_query_name='genes', related_name='result', on_delete=models.CASCADE)
    aro_gene = models.ForeignKey(AroGene, related_name='result', on_delete=models.PROTECT)
    identifier = models.CharField(max_length=2555)
    contig = models.CharField(max_length=255)
    type_match = models.CharField(editable=False, choices=TYPE_MATCH, max_length=10)
    orf_strand = models.CharField(max_length=1, editable=False)
    orf_start = models.IntegerField(editable=False)
    orf_end = models.IntegerField(editable=False)
    orf_from = models.CharField(editable=False, max_length=2500)
    pass_evalue = models.CharField(editable=False, max_length=255)
    pass_bitscore = models.CharField(editable=False, max_length=255)
    evalue = models.FloatField(editable=False)
    max_identities = models.IntegerField(editable=False)
    bit_score = models.FloatField(editable=False)
    cvterm_id = models.CharField(editable=False, max_length=255)
    query = models.CharField(editable=False, max_length=5000)
    match = models.CharField(editable=False, max_length=5000)
    sequence_from_db = models.CharField(editable=False, max_length=5000)
    sequence_from_broadstreet = models.CharField(editable=False, max_length=5000)
    dna_sequence_from_broadstreet = models.CharField(editable=False, max_length=5000)
    query_start = models.IntegerField(editable=False)
    query_end = models.IntegerField(editable=False)
    orf_dna_sequence = models.CharField(editable=False, max_length=5000)
    orf_prot_sequence = models.CharField(editable=False, max_length=5000)
    perc_identity = models.FloatField(editable=False)
    nudged = models.BooleanField(editable=False, default=False)

    @classmethod
    def from_rgi_result(cls, contig_hits, result):
        hit = sorted(contig_hits.values(), key=lambda k: k['bit_score'])[-1]
        contig = hit['orf_from']
        aro_gene = AroGene.objects.get(model_id=hit['model_id'])
        creation_values = {key.lower(): hit[key]
                           for key in hit if key not in [
                               'model_id',
                               'model_name',
                               'model_type',
                               'model_type_id',
                               'ARO_accession',
                               'ARO_name',
                               'ARO_category',
                               'note'

                           ]
                           }
        cls.objects.create(contig=contig, aro_gene=aro_gene, result=result, **creation_values)


    @classmethod
    def from_rgi_result_randomize(cls, contig_hits, result):
        qs = AroGene.objects.all()
        hit = sorted(contig_hits.values(), key=lambda k: k['bit_score'])[-1]
        contig = hit['orf_from']
        aro_gene = qs[random.randint(0, qs.aggregate(count=Count('pk'))['count'] - 1)]
        creation_values = {key.lower(): hit[key]
                           for key in hit if key not in [
                               'model_id',
                               'model_name',
                               'model_type',
                               'model_type_id',
                               'ARO_accession',
                               'ARO_name',
                               'ARO_category']
                           }
        cls.objects.create(contig=contig, aro_gene=aro_gene, result=result, **creation_values)


@receiver(models.signals.post_delete, sender=Species)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.sequence_file:
        if os.path.isfile(instance.sequence_file.path):
            os.remove(instance.sequence_file.path)

@receiver(models.signals.post_delete, sender=Sequence)
def auto_delete_file_on_delete2(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.sequence_file_pair1:
        if os.path.isfile(instance.sequence_file_pair1.path):
            os.remove(instance.sequence_file_pair1.path)
    if instance.sequence_file_pair2:
        if os.path.isfile(instance.sequence_file_pair2.path):
            os.remove(instance.sequence_file_pair2.path)


@receiver(models.signals.pre_save, sender=Species)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `Sequence` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = Sequence.objects.get(pk=instance.pk).sequence_file
    except Sequence.DoesNotExist:
        return False

    new_file = instance.sequence_file
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
