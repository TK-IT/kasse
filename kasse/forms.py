from __future__ import absolute_import, unicode_literals, division

import re
import datetime

from django import forms

from kasse.models import Profile
from kasse.fields import DateTimeDefaultTodayField


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    next = forms.CharField(widget=forms.HiddenInput)


class TimeTrialCreateForm(forms.Form):
    profile = forms.ModelChoiceField(
        queryset=Profile.objects.all())
    result = forms.ChoiceField(
        choices=TimeTrial.RESULTS)
    durations = forms.CharField(
        widget=forms.Textarea)
    start_time = DateTimeDefaultTodayField(
        required=False, label='Starttidspunkt')

    def clean_durations(self):
        data = self.cleaned_data['durations']
        pattern = r'(?:(?P<minutes>[0-9]+):)?(?P<seconds>[0-9]+\.?[0-9]*)$'
        durations = []
        for e in data.split():
            mo = re.match(pattern, e)
            if not mo:
                raise forms.ValidationError(
                    '%r er ugyldig' % e)
            m = mo.group('minutes') or '0'
            s = mo.group('seconds')
            d = datetime.timedelta(minutes=int(m), seconds=float(s))
            durations.append(d)
        return durations

    def clean(self):
        cleaned_data = super(TimeTrialCreateForm, self).clean()
        if not cleaned_data.get('start_time'):
            cleaned_data['start_time'] = datetime.datetime.now()
        return cleaned_data
