# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import datetime

from django import forms
from django.utils import timezone

from multiupload.fields import MultiFileField

from stopwatch.models import TimeTrial
from stopwatch.fields import DateTimeDefaultTodayField, DurationListField
from kasse.forms import ProfileModelChoiceField
from kasse.models import Profile


class TimeTrialCreateForm(forms.Form):
    CHOICES = (
        ('individual', 'Tider på de enkelte øl'),
        ('total', 'Samlet tid'),
        ('stopwatch', 'Stopur'),
    )

    profile = ProfileModelChoiceField(label='Person')
    dnf = forms.BooleanField(required=False, label='DNF')
    individual_times = forms.ChoiceField(
        choices=CHOICES, widget=forms.RadioSelect, initial='individual')
    stopwatch = forms.BooleanField(required=False, label='Stopur')

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
            cleaned_data['start_time'] = timezone.now()

        individual_times = cleaned_data['individual_times']
        if cleaned_data['stopwatch']:
            cleaned_data['individual_times'] = 'stopwatch'
        elif individual_times == 'individual':
            self.check_required(cleaned_data, 'durations')
        elif individual_times == 'total':
            self.check_required(cleaned_data, 'legs')
            self.check_required(cleaned_data, 'total_time')
        return cleaned_data

    def check_required(self, cleaned_data, field_name):
        v = cleaned_data.get(field_name)
        if not v:
            field = self.fields[field_name]
            self.add_error(field_name, field.error_messages['required'])


class TimeTrialLiveForm(forms.Form):
    STATES = TimeTrial.STATES
    timetrial = forms.ModelChoiceField(TimeTrial.objects.all())

    durations = DurationListField(required=False)
    elapsed_time = forms.DurationField()
    roundtrip_estimate = forms.FloatField(initial=0)
    possible_laps = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': '5', 'cols': '20'}))
    state = forms.ChoiceField(choices=STATES)


class StopwatchForm(forms.Form):
    CHOICES = (
        ('f', 'Gyldig'),
        ('dnf', 'DNF'),
        ('irr', 'Ugyldig/uregelmæssig'),  # not accepted / irregular result
    )

    start_time = forms.FloatField()
    result = forms.ChoiceField(
        choices=CHOICES, widget=forms.RadioSelect, initial='f')
    durations = DurationListField(
        required=False,
        widget=forms.Textarea(attrs={'rows': '5', 'cols': '20'}))

    residue = forms.FloatField(required=False)
    comment = forms.CharField(required=False)
    beverage = forms.CharField(required=False)

    images = MultiFileField(required=False)

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance')
        kwargs['initial']['durations'] = list(instance.leg_set.all())
        super(StopwatchForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(StopwatchForm, self).clean()
        if 'start_time' in cleaned_data:
            start_time = cleaned_data['start_time']
            if start_time < 0:
                start_time += 2 ** 32
            cleaned_data['start_time'] = (
                datetime.datetime.utcfromtimestamp(
                    start_time).replace(tzinfo=timezone.utc))
        return cleaned_data


class TimeTrialForm(forms.ModelForm):
    class Meta:
        model = TimeTrial
        fields = ('profile', 'state', 'result', 'start_time',
                  'comment', 'residue')

    durations = DurationListField(
        required=False,
        widget=forms.Textarea(attrs={'rows': '5', 'cols': '20'}))

    def __init__(self, *args, **kwargs):
        instance = kwargs['instance']
        kwargs['initial']['durations'] = list(instance.leg_set.all())
        super(TimeTrialForm, self).__init__(*args, **kwargs)

    def save(self):
        instance = super(TimeTrialForm, self).save(commit=False)
        instance.save_robust()
        instance.set_legs(
            [d.total_seconds() for d in self.cleaned_data['durations']])
        return instance
