# Generated by Django 2.0.5 on 2018-06-27 18:58

import Isolates.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Isolates', '0002_auto_20180626_1501'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='isolate',
            options={'ordering': ['collection_date']},
        ),
        migrations.AddField(
            model_name='sequence',
            name='assembly_file',
            field=models.FileField(null=True, upload_to=Isolates.models.isolates.sequence_directory_path, validators=[
                Isolates.models.isolates.fa_validate_file_extension]),
        ),
    ]
