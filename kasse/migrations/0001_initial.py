# -*- coding: utf-8 -*-
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
            ],
        ),
        migrations.CreateModel(
            name='Leg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('duration', models.FloatField()),
                ('order', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, blank=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('association', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='kasse.Association')),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TimeTrial',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('duration', models.FloatField()),
                ('result', models.CharField(blank=True, max_length=10, choices=[('f', 'Finished'), ('dnf', 'DNF')])),
                ('start_time', models.DateTimeField()),
                ('created_time', models.DateTimeField()),
                ('creator', models.ForeignKey(related_name='timetrial_creator_set', to='kasse.Profile')),
                ('profile', models.ForeignKey(related_name='timetrial_profile_set', to='kasse.Profile')),
            ],
        ),
        migrations.AddField(
            model_name='leg',
            name='timetrial',
            field=models.ForeignKey(to='kasse.TimeTrial'),
        ),
    ]
