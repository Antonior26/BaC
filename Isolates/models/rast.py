from django.db import models


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


