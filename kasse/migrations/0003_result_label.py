# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0002_timetrial_start_time_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timetrial',
            name='result',
            field=models.CharField(blank=True, max_length=10, choices=[('f', '\u2713'), ('dnf', 'DNF')]),
        ),
    ]
