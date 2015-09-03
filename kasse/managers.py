# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.db import models
from django.db.models import Count, Sum
from django.db.models.expressions import RawSQL


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


class LegManagerPrototype(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(LegManagerPrototype, self).get_queryset()
        sql = '''
            SELECT SUM(duration) FROM kasse_leg `a`
            WHERE a.timetrial_id = kasse_leg.timetrial_id
            AND a.order <= kasse_leg.order'''
        qs = qs.annotate(p=RawSQL(sql, ()))
        return qs
