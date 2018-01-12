# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import json

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.db import models, OperationalError
from django.db.models import Sum

from kasse.models import Profile

from stopwatch.managers import (
    TimeTrialManager, LegManager,
)


@python_2_unicode_compatible
class TimeTrial(models.Model):
    objects = TimeTrialManager()
    raw_objects = models.Manager()

    @classmethod
    def leg_prefix(cls, n):
        qs = cls.raw_objects.filter(leg__order__lt=n + 1)
        qs = TimeTrialManager.process_queryset(qs).filter(leg_count=n)
        qs = qs.filter(duration__gt=0)
        return qs

    RESULTS = (
        ('f', 'Finished'),
        ('irr', 'Not accepted'),  # not accepted / irregular result
        ('dnf', 'Did not finish'),
    )
    STATES = (
        ('running', 'I gang'),
        ('stopped', 'Stoppet'),
        ('initial', 'Parat'),
    )
    profile = models.ForeignKey(
        Profile, related_name='timetrial_profile_set')
    state = models.CharField(max_length=10, choices=STATES, default='initial')
    result = models.CharField(max_length=10, choices=RESULTS, blank=True)
    start_time = models.DateTimeField(blank=True, null=True)

    comment = models.TextField(blank=True)
    residue = models.FloatField(null=True, blank=True)

    creator = models.ForeignKey(
        Profile, related_name='timetrial_creator_set')
    created_time = models.DateTimeField()

    beverage = models.ForeignKey(
        'Beverage', blank=True, null=True, on_delete=models.SET_NULL)

    possible_laps = models.TextField(blank=True)

    def parse_possible_laps(self):
        if not self.possible_laps:
            return []
        try:
            laps = json.loads(self.possible_laps)
        except json.JSONDecodeError:
            raise ValidationError('possible_laps is not valid JSON')

        def parse_lap(lap):
            if not isinstance(lap, dict):
                raise ValidationError('lap is not a dict')
            if lap.keys() != {'time', 'lap', 'comment'}:
                raise ValidationError('lap has wrong keys')
            return dict(seconds=lap['time'] / 1000,
                        lap=lap['lap'],
                        comment=lap['comment'])

        return [parse_lap(o) for o in laps]

    def get_result_mark(self):
        if self.result == 'f':
            return '✓'
        elif self.result == 'irr':
            return '#'
        elif self.result == 'dnf':
            return 'DNF'
        else:
            return self.result

    def get_duration_display(self):
        try:
            d = self.duration
        except AttributeError:
            d = self.compute_duration()
        if d is None:
            return 'None'
        else:
            minutes, seconds = divmod(d, 60)
            return '%d:%05.2f' % (minutes, seconds)

    def compute_duration(self):
        return self.leg_set.all().aggregate(d=Sum('duration'))['d']

    def clean(self):
        pass

    def set_legs(self, durations):
        legs = [Leg(timetrial=self, duration=d, order=i + 1)
                for i, d in enumerate(durations)]
        self.leg_set.all().delete()
        for l in legs:
            l.save()

    def __str__(self):
        if self.result == '':
            state = self.state.upper()
        else:
            state = self.get_result_display()
        return '[TimeTrial: %s %s on %s by %s]' % (
            self.get_duration_display(), state, self.start_time, self.profile)

    def get_absolute_url(self):
        return reverse('timetrial_detail', kwargs={'pk': self.pk})

    def save_robust(self):
        try:
            self.save()
        except OperationalError:
            # Work around bug in SQLite
            # Related to: https://code.djangoproject.com/ticket/18580
            TimeTrial.objects.filter(pk=self.pk).values('id').update(
                profile=self.profile,
                state=self.state,
                result=self.result,
                start_time=self.start_time,
                comment=self.comment,
                residue=self.residue,
                creator=self.creator,
                created_time=self.created_time,
                beverage=self.beverage,
                possible_laps=self.possible_laps,
            )

    class Meta:
        ordering = ['-created_time']


@python_2_unicode_compatible
class Leg(models.Model):
    objects = LegManager()
    raw_objects = models.Manager()

    timetrial = models.ForeignKey(TimeTrial)
    duration = models.FloatField()
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.duration)

    class Meta:
        ordering = ['timetrial', 'order']


def move_profile(target, destination):
    TimeTrial.objects.filter(profile=target).update(profile=destination)
    TimeTrial.objects.filter(creator=target).update(creator=destination)


@python_2_unicode_compatible
class Beverage(models.Model):
    name = models.CharField(max_length=50, unique=True)
    popularity = models.IntegerField(default=0)

    class Meta:
        ordering = ['popularity', 'name']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Image(models.Model):
    timetrial = models.ForeignKey(TimeTrial, models.CASCADE)
    image = models.ImageField(
        upload_to='timetrial',
        height_field='height',
        width_field='width',
    )
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s" % (self.image,)
