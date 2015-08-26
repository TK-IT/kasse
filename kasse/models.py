# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.contrib.auth.models import User


@python_2_unicode_compatible
class Association(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Profile(models.Model):
    user = models.OneToOneField(User, null=True, blank=True,
                                on_delete=models.SET_NULL)
    name = models.CharField(max_length=200, blank=True)
    association = models.ForeignKey(Association, null=True, blank=True,
                                    on_delete=models.SET_NULL)

    created_time = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.user and not self.name:
            raise ValidationError('Name is required for non-anonymous profile')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class TimeTrial(models.Model):
    RESULTS = (
        ('f', '✓'),
        ('dnf', 'DNF'),
    )
    profile = models.ForeignKey(
        Profile, related_name='timetrial_profile_set')
    duration = models.FloatField()
    result = models.CharField(max_length=10, choices=RESULTS, blank=True)
    start_time = models.DateTimeField(blank=True, null=True)

    creator = models.ForeignKey(
        Profile, related_name='timetrial_creator_set')
    created_time = models.DateTimeField()

    def clean(self):
        self.duration = sum(l.duration for l in self.leg_set.all())

    def __str__(self):
        return '[TimeTrial: %s s on %s by %s]' % (
            self.duration, self.start_time, self.profile)

    class Meta:
        ordering = ['start_time', 'created_time']


@python_2_unicode_compatible
class Leg(models.Model):
    timetrial = models.ForeignKey(TimeTrial)
    duration = models.FloatField()
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.duration)

    class Meta:
        ordering = ['timetrial', 'order']
