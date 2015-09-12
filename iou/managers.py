# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.db import models
from django.db.models import Count, Sum, F, ExpressionWrapper

from kasse.managers import ProfileManager as ProfileManagerBase


class ProfileManager(ProfileManagerBase):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(ProfileManager, self).get_queryset()
        # balance = (
        #     Sum(F('expence_consumed_set__amount') /
        #         Count('expence_consumed_set__consumers')))
        # qs = qs.annotate(balance=balance)
        # print(qs.query)
        return qs


class ExpenceManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(ExpenceManager, self).get_queryset()
        amount_field = qs.model._meta.get_field('amount')
        amount_each = ExpressionWrapper(F('amount') / Count('consumers'),
                                        output_field=amount_field)
        qs = qs.annotate(amount_each=amount_each)
        return qs
