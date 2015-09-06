# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0005_timetrial_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetrial',
            name='comment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='timetrial',
            name='residue',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
