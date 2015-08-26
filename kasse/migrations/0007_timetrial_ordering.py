# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0006_add_title_models'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='timetrial',
            options={'ordering': ['-created_time']},
        ),
    ]
