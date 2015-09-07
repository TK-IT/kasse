# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.db.models import Sum

from kasse.models import Profile

from stopwatch.managers import (
    TimeTrialManager, LegManager,
)


@python_2_unicode_compatible
class TimeTrial(models.Model):
    objects = TimeTrialManager()

    RESULTS = (
        ('f', '✓'),
        ('dnf', 'DNF'),
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

    def __str__(self):
        if self.result == 'dnf':
            state = 'DNF '
        elif self.result == '':
            state = ('%s ' % self.state).upper()
        else:
            state = ''
        return '[TimeTrial: %s %son %s by %s]' % (
            self.get_duration_display(), state, self.start_time, self.profile)

    class Meta:
        ordering = ['-created_time']


@python_2_unicode_compatible
class Leg(models.Model):
    objects = LegManager()

    timetrial = models.ForeignKey(TimeTrial)
    duration = models.FloatField()
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.duration)

    class Meta:
        ordering = ['timetrial', 'order']