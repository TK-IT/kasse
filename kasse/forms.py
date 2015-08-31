# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import re
import datetime

from django import forms

from kasse.models import Profile, Association
from kasse.fields import DateTimeDefaultTodayField, DurationListField


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    next = forms.CharField(widget=forms.HiddenInput)


class ProfileModelChoiceField(forms.ModelChoiceField):
    def __init__(self, **kwargs):
        kwargs.setdefault('queryset', Profile.all_named())
        super(ProfileModelChoiceField, self).__init__(**kwargs)

    def label_from_instance(self, obj):
        if obj.is_anonymous:
            return '%s' % (obj,)
        elif obj.association:
            return '%s (%s)' % (obj, obj.association)
        else:
            return '%s (independent)' % (obj,)


class TimeTrialCreateForm(forms.Form):
    CHOICES = (
        ('individual', 'Tider på de enkelte øl'),
        ('total', 'Samlet tid'),
    )

    profile = ProfileModelChoiceField(label='Person')
    dnf = forms.BooleanField(required=False, label='DNF')
    individual_times = forms.ChoiceField(
        required=False,
        choices=CHOICES, widget=forms.RadioSelect, initial='individual')

    durations = DurationListField(
        required=False,
        widget=forms.Textarea(attrs={'rows': '5', 'cols': '20'}))

    legs = forms.IntegerField(
        initial=5,
        required=False, label="Antal øl", min_value=1, max_value=100)
    total_time = forms.DurationField(required=False, label="Samlet tid")

    start_time = DateTimeDefaultTodayField(
        required=False, label='Starttidspunkt')
    start_time_unknown = forms.BooleanField(required=False, label='Ukendt')

    def clean(self):
        cleaned_data = super(TimeTrialCreateForm, self).clean()
        dnf = cleaned_data.pop('dnf')
        cleaned_data['result'] = 'dnf' if dnf else 'f'
        unknown = cleaned_data['start_time_unknown']
        if cleaned_data.get('start_time') and unknown:
            self.add_error(
                'start_time',
                'Man kan ikke angive både starttidspunkt og ukendt.')
        elif not cleaned_data.get('start_time') and not unknown:
            cleaned_data['start_time'] = datetime.datetime.now()

        individual_times = cleaned_data['individual_times']
        if individual_times == 'individual':
            self.check_required(cleaned_data, 'durations')
        elif individual_times == 'total':
            self.check_required(cleaned_data, 'legs')
            self.check_required(cleaned_data, 'total_time')
        return cleaned_data

    def check_required(self, cleaned_data, field_name):
        v = cleaned_data.get(field_name)
        if not v:
            field = self.fields[field_name]
            self.add_error(field_name, field.error_messages[field_name])


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
