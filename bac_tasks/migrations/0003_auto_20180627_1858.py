# Generated by Django 2.0.5 on 2018-06-27 18:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bac_tasks', '0002_auto_20180626_1501'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='componenttask',
            options={'ordering': ['last_update_date']},
        ),
    ]
