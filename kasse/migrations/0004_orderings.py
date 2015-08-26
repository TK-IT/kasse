# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0003_result_label'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='leg',
            options={'ordering': ['timetrial', 'order']},
        ),
        migrations.AlterModelOptions(
            name='timetrial',
            options={'ordering': ['start_time', 'created_time']},
        ),
    ]
