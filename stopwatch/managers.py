# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.db import models
from django.db.models import Count, Sum, F, ExpressionWrapper, Case, When
from django.db.models import DurationField, DateTimeField


def seconds_to_duration(e):
    return ExpressionWrapper(1000000 * e, output_field=DurationField())


class TimeTrialManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(TimeTrialManager, self).get_queryset()
        return self.process_queryset(qs)

    @classmethod
    def process_queryset(cls, qs):
        qs = qs.annotate(leg_count=Count('leg'))
        qs = qs.annotate(duration=Sum('leg__duration'))

        created_time = F('created_time')
        start_time = F('start_time')
        stop_time = ExpressionWrapper(
            F('start_time') + seconds_to_duration(F('duration')),
            output_field=DateTimeField())
        last_activity = Case(
            When(leg_count__gt=0, then=stop_time),
            When(start_time__isnull=True, then=created_time),
            default=start_time)
        qs = qs.annotate(last_activity=last_activity)
        return qs.select_related('profile', 'creator')


class LegManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(LegManager, self).get_queryset()

        # Add the annotation `duration_prefix_sum`
        # which is the sum of Leg.duration for the other Legs
        # of the TimeTrial which has order <= this Leg's order.
        qs = qs.filter(timetrial__leg__order__lte=F('order'))
        qs = qs.annotate(duration_prefix_sum=Sum('timetrial__leg__duration'))

        dur = seconds_to_duration(F('duration_prefix_sum'))
        time = ExpressionWrapper(
            F('timetrial__start_time') + dur, output_field=DateTimeField())
        qs = qs.annotate(time=time)

        return qs
