# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.core.urlresolvers import reverse
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
        if self.result == 'dnf':
            state = 'DNF '
        elif self.result == '':
            state = ('%s ' % self.state).upper()
        else:
            state = ''
        return '[TimeTrial: %s %son %s by %s]' % (
            self.get_duration_display(), state, self.start_time, self.profile)

    def get_absolute_url(self):
        return reverse('timetrial_detail', kwargs={'pk': self.pk})

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
