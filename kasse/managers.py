# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.db import models
from django.db.models import CharField, Case, Value, When, F
from django.db.models.functions import Concat


def get_display_title(path):
    current_period = F(path + 'association__current_period')
    period = F(path + 'period')
    title = F(path + 'title')

    def path_when(k, v, **kwargs):
        kwargs[path + k] = v
        return When(**kwargs)

    k_gt = path_when(
        'period__gt', current_period + Value(1),
        then=Concat(Value('K'), period - current_period, title))
    k = path_when(
        'period', current_period + Value(1),
        then=Concat(Value('K'), title))
    current = path_when(
        'period', current_period,
        then=title)
    g = path_when(
        'period', current_period - Value(1),
        then=Concat(Value('G'), title))
    b = path_when(
        'period', current_period - Value(2),
        then=Concat(Value('B'), title))
    o = path_when(
        'period', current_period - Value(3),
        then=Concat(Value('O'), title))
    to = path_when(
        'period', current_period - Value(4),
        then=Concat(Value('TO'), title))
    tno = path_when(
        'period__lt', current_period - Value(4),
        then=Concat(Value('T'), current_period - period - Value(3),
                    Value('O'), title))
    tk_title = Case(
        k_gt, k, current, g, b, o, to, tno,
        default=path + 'title', output_field=CharField())

    def_title = Case(
        path_when('period__isnull', False,
                  then=Concat(title, Value(' '), period)),
        default=path + 'title', output_field=CharField())

    return Case(
        path_when('association__name', 'TÅGEKAMMERET', then=tk_title),
        default=def_title, output_field=CharField())


class ProfileManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(ProfileManager, self).get_queryset()
        title = get_display_title('title__')
        qs = qs.annotate(
            display_name=Case(
                When(title__isnull=True, name='',
                     then=Concat(Value('(anonymous '), F('id'), Value(')'))),
                When(title__isnull=True, then='name'),
                When(name='', then=title),
                default=Concat(title, Value(' '), F('name')),
                output_field=CharField()))
        return qs.select_related('association', 'title__association')
