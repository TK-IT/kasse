# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import re

from django.core.exceptions import ValidationError
from django import forms
from django.utils import six


class TKPeriodField(forms.IntegerField):
    def clean(self, value):
        period = super(TKPeriodField, self).clean(value)
        if period and period < 1956:
            raise ValidationError('Periode skal være et 4-cifret årstal')
        return period


class APeriodField(forms.CharField):
    @staticmethod
    def static_prepare_value(value):
        if not value:
            return value
        if isinstance(value, str):
            try:
                value = int(value)
            except:
                return value
        if isinstance(value, six.integer_types):
            year, semester = divmod(value % 100, 2)
            return '%s%02d' % ('FE'[semester], year)
        return value

    def prepare_value(self, value):
        return self.static_prepare_value(value)

    def clean(self, value):
        value = super(APeriodField, self).clean(value)
        if not value:
            return value
        mo = re.match(r'^([FE])(\d\d)$', value)
        if not mo:
            raise ValidationError(
                'Periode skal være F eller E efterfulgt af to-cifret årstal')
        value = 2 * int(mo.group(2))
        if mo.group(1) == 'E':
            value += 1
        return value
