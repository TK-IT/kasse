# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0003_profile_favorite_drink'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='favorite_drink',
            field=models.CharField(max_length=200, verbose_name='Yndlings\xf8l', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Navn', blank=True),
        ),
    ]
