# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import re
import datetime

from django import forms

from kasse.models import Profile, Association
from kasse.fields import DateTimeDefaultTodayField


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    next = forms.CharField(widget=forms.HiddenInput)


class TimeTrialCreateForm(forms.Form):
    profile = forms.ModelChoiceField(
        queryset=Profile.objects.all(),
        label='Person')
    dnf = forms.BooleanField(required=False, label='DNF')
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
        dnf = cleaned_data.pop('dnf')
        cleaned_data['result'] = 'dnf' if dnf else 'f'
        if not cleaned_data.get('start_time'):
            cleaned_data['start_time'] = datetime.datetime.now()
        return cleaned_data


class ProfileCreateForm(forms.Form):
    name = forms.CharField(required=False, label='Navn')
    title = forms.CharField(required=False, label='Titel')
    period = forms.IntegerField(required=False, label='Periode')
    association = forms.ModelChoiceField(
        Association.objects.all(), required=False,
        empty_label=Association.none_string(), label='Tilknytning')

    def clean(self):
        cleaned_data = super(ProfileCreateForm, self).clean()
        name = cleaned_data['name']
        title = cleaned_data['title']
        association = cleaned_data['association']
        if not name and not title:
            self.add_error('name', 'Navn er påkrævet.')
        if title and not association:
            self.add_error('association', 'Titel kræver en tilknytning.')
