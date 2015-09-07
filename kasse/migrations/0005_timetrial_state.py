# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0004_profile_field_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetrial',
            name='state',
            field=models.CharField(default='initial', max_length=10,
                                   choices=[('running', 'I gang'),
                                            ('stopped', 'Stoppet'),
                                            ('initial', 'Parat')]),
        ),
    ]
