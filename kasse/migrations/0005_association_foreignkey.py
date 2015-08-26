# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0004_orderings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='association',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='kasse.Association', null=True),
        ),
    ]
