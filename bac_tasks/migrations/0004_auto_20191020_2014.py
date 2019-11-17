# Generated by Django 2.0.5 on 2019-10-20 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bac_tasks', '0003_auto_20180627_1858'),
    ]

    operations = [
        migrations.AlterField(
            model_name='componenttask',
            name='component_type',
            field=models.CharField(choices=[('QC', 'QC'), ('ASSEMBLY', 'ASSEMBLY'), ('ALIGNMENT', 'ALIGNMENT'), ('VARIANT_CALLING', 'VARIANT_CALLING'), ('ANNOTATION', 'ANNOTATION'), ('COVERAGE', 'COVERAGE'), ('RESISTANCE_ANALYSIS', 'RESISTANCE_ANALYSIS'), ('VIRULENCE_ANALYSIS', 'VIRULENCE_ANALYSIS')], editable=False, max_length=250),
        ),
    ]