# Generated by Django 2.0.5 on 2019-11-17 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Isolates', '0007_auto_20191020_2014'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='type',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
