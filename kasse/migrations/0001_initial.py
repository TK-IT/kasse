# -*- coding: utf-8 -*-
# flake8: noqa
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Association',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('current_period', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Leg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('duration', models.FloatField()),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['timetrial', 'order'],
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, blank=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('association', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='kasse.Association', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TimeTrial',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('duration', models.FloatField()),
                ('result', models.CharField(blank=True, max_length=10, choices=[('f', '\u2713'), ('dnf', 'DNF')])),
                ('start_time', models.DateTimeField(null=True, blank=True)),
                ('created_time', models.DateTimeField()),
                ('creator', models.ForeignKey(related_name='timetrial_creator_set', to='kasse.Profile')),
                ('profile', models.ForeignKey(related_name='timetrial_profile_set', to='kasse.Profile')),
            ],
            options={
                'ordering': ['-created_time'],
            },
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('period', models.IntegerField(null=True, blank=True)),
                ('title', models.CharField(max_length=200)),
                ('association', models.ForeignKey(to='kasse.Association')),
            ],
        ),
        migrations.AddField(
            model_name='profile',
            name='title',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='kasse.Title'),
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='leg',
            name='timetrial',
            field=models.ForeignKey(to='kasse.TimeTrial'),
        ),
    ]
