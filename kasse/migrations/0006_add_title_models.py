# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0005_association_foreignkey'),
    ]

    operations = [
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('period', models.IntegerField(null=True, blank=True)),
                ('title', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='association',
            name='current_period',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='title',
            name='association',
            field=models.ForeignKey(to='kasse.Association'),
        ),
        migrations.AddField(
            model_name='profile',
            name='title',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='kasse.Title'),
        ),
    ]
