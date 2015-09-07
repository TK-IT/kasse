# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_data(apps, schema_editor):
    TimeTrialA = apps.get_model('kasse', 'TimeTrial')
    TimeTrialB = apps.get_model('stopwatch', 'TimeTrial')
    LegA = apps.get_model('kasse', 'Leg')
    LegB = apps.get_model('stopwatch', 'Leg')

    # dict mapping old pk to new object
    timetrials = {}
    for a in TimeTrialA.objects.all():
        b = TimeTrialB(
            state=a.state,
            result=a.result,
            start_time=a.start_time,
            comment=a.comment,
            residue=a.residue,
            created_time=a.created_time,
            creator=a.creator,
            profile=a.profile)
        b.save()
        # Note, we cannot bulk create TimeTrial, as we need all new pks
        timetrials[a.pk] = b

    legs = []
    for a in LegA.objects.all():
        b = LegB(
            duration=a.duration,
            order=a.order,
            timetrial=timetrials[a.timetrial_id])
        legs.append(b)
    LegB.objects.bulk_create(legs)


def copy_data_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('kasse', '0006_timetrial_comment_residue'),
    ]

    operations = [
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
            name='TimeTrial',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.CharField(default='initial', max_length=10, choices=[('running', 'I gang'), ('stopped', 'Stoppet'), ('initial', 'Parat')])),
                ('result', models.CharField(blank=True, max_length=10, choices=[('f', '\u2713'), ('dnf', 'DNF')])),
                ('start_time', models.DateTimeField(null=True, blank=True)),
                ('comment', models.TextField(blank=True)),
                ('residue', models.FloatField(null=True, blank=True)),
                ('created_time', models.DateTimeField()),
                ('creator', models.ForeignKey(related_name='timetrial_creator_set', to='kasse.Profile')),
                ('profile', models.ForeignKey(related_name='timetrial_profile_set', to='kasse.Profile')),
            ],
            options={
                'ordering': ['-created_time'],
            },
        ),
        migrations.AddField(
            model_name='leg',
            name='timetrial',
            field=models.ForeignKey(to='stopwatch.TimeTrial'),
        ),
        migrations.RunPython(copy_data, copy_data_reverse),
    ]
