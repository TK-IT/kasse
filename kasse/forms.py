from __future__ import absolute_import, unicode_literals, division

import re
import datetime

from django import forms

from kasse.models import Profile, TimeTrial


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
    start_time = forms.DateTimeField(required=False)

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
