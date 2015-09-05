# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.db import models
from django.db.models import Count, Sum, F
from django.db.models.sql.where import AND
from django.db.models.lookups import LessThanOrEqual


class ProfileManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(ProfileManager, self).get_queryset()
        return qs.select_related('association', 'title__association')


class TimeTrialManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(TimeTrialManager, self).get_queryset()
        qs = qs.annotate(leg_count=Count('leg'))
        qs = qs.annotate(duration=Sum('leg__duration'))
        return qs.select_related('profile', 'creator')


class LegManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(LegManager, self).get_queryset()

        # Add the annotation `duration_prefix_sum`
        # which is the sum of Leg.duration for the other Legs
        # of the TimeTrial which has order <= this Leg's order.

        # First, add a Sum-annotation that sums all durations.
        qs = qs.annotate(duration_prefix_sum=Sum('timetrial__leg__duration'))

        # Add a condition to the query WHERE-clause
        # to ensure that other_order is less or equal to my_order.
        my_order = F('order').resolve_expression(query=qs.query)
        other_order = F('timetrial__leg__order')
        other_order = other_order.resolve_expression(query=qs.query)
        lte_cond = LessThanOrEqual(other_order, my_order)

        qs.query.where.add(lte_cond, AND)

        return qs
