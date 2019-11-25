from bac_tasks.pipelines.assembly import Assembly
from bac_tasks.pipelines.annotation import Annotation
from bac_tasks.pipelines.virulence_analysis import Virulence
from bac_tasks.pipelines.resistance_analysis import Resistance
from bac_tasks.pipelines.seq_mash import SeqMash


COMPONENT_TYPES = (
    ('QC', 'QC'),
    ('ASSEMBLY', 'ASSEMBLY'),
    ('ALIGNMENT', 'ALIGNMENT'),
    ('VARIANT_CALLING', 'VARIANT_CALLING'),
    ('ANNOTATION', 'ANNOTATION'),
    ('COVERAGE', 'COVERAGE'),
    ('RESISTANCE_ANALYSIS', 'RESISTANCE_ANALYSIS'),
    ('VIRULENCE_ANALYSIS', 'VIRULENCE_ANALYSIS'),
    ('REFSEQ_MASHER', 'REFSEQ_MASHER'),
)
