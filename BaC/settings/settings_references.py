import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_RESULTS = os.getenv('BAC_REFERENCE', os.path.join(BASE_DIR, 'reference'))
SEQUENCE_RESULTS = os.getenv('BAC_SEQUENCE_RESULTS', os.path.join(BASE_DIR, 'reference', 'sequence_results'))


ASSEMBLY_PATHS = dict(
    spades_path=os.getenv('BAC_SPADES_PATH', '/home/aruedamartin/SPAdes-3.12.0/SPAdes-3.12.0-Linux/bin/spades.py'),
    velveth_path=os.getenv('BAC_VELVETH_PATH', 'velveth'),
    velvetg_path=os.getenv('BAC_VELVETG_PATH', 'velvetg'),
    qc_path=os.getenv('BAC_QC_PATH', ''),
)


ANNOTATION_PATHS = dict(
    rast_create_genome=os.getenv('BAC_RAST_CREATE_GENOME', 'rast-create-genome'),
    rast_process_genome=os.getenv('BAC_RAST_PROCESS_GENOME', 'rast-process-genome'),
    rast_export_genome=os.getenv('BAC_RAST_EXPORT_GENOME', 'rast-export-genome'),

)

RGI_PATHS = dict(
    rgi_path=os.getenv('BAC_RGI_PATH', 'rgi'),
    db_path=os.getenv('BAC_DB_PATH', '/home/aruedamartin/PycharmAntonio/BaC/reference'),
)
