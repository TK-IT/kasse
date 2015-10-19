# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.db import models
from django.db.models import CharField, Case, Value, When, F
from django.db.models.functions import Concat


class ProfileManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(ProfileManager, self).get_queryset()
        qs = qs.annotate(
            display_name=Case(
                When(title__isnull=True, name='',
                     then=Concat(Value('(anonymous '), F('id'), Value(')'))),
                When(title__isnull=True, then='name'),
                When(name='', then='title__title'),
                default=Concat(F('title__title'), Value(' '), F('name')),
                output_field=CharField()))
        return qs.select_related('association', 'title__association')
