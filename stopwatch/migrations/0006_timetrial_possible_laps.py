# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-02-06 12:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stopwatch', '0005_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetrial',
            name='possible_laps',
            field=models.TextField(blank=True),
        ),
    ]
