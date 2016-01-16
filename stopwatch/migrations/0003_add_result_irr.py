# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-16 08:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stopwatch', '0002_unabbreviate_results'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timetrial',
            name='result',
            field=models.CharField(blank=True, choices=[('f', 'Finished'), ('irr', 'Not accepted'), ('dnf', 'Did not finish')], max_length=10),
        ),
    ]
