# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0002_remove_timetrial_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='favorite_drink',
            field=models.CharField(max_length=200, blank=True),
        ),
    ]
