# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0006_timetrial_comment_residue'),
        ('stopwatch', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='leg',
            name='timetrial',
        ),
        migrations.RemoveField(
            model_name='timetrial',
            name='creator',
        ),
        migrations.RemoveField(
            model_name='timetrial',
            name='profile',
        ),
        migrations.DeleteModel(
            name='Leg',
        ),
        migrations.DeleteModel(
            name='TimeTrial',
        ),
    ]
