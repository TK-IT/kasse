# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-26 19:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stopwatch', '0006_timetrial_possible_laps'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetrial',
            name='is_kasse_i_kass',
            field=models.BooleanField(default=False),
        ),
    ]
