# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0007_delete_stopwatch_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='Expence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(max_digits=9, decimal_places=2)),
                ('comment', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExpenceProfile',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('kasse.profile',),
        ),
        migrations.AddField(
            model_name='expence',
            name='consumers',
            field=models.ManyToManyField(related_name='expence_consumed_set', to='kasse.Profile'),
        ),
        migrations.AddField(
            model_name='expence',
            name='payer',
            field=models.ForeignKey(related_name='expence_paid_set', to='kasse.Profile'),
        ),
    ]
