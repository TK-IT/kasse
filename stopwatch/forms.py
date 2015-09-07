# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import datetime

from django import forms
from django.forms.utils import to_current_timezone

from stopwatch.models import TimeTrial
from stopwatch.fields import DateTimeDefaultTodayField, DurationListField
from kasse.models import Profile


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


def label_placeholder(cls):
    for f in cls.base_fields.values():
        f.widget.attrs.setdefault('placeholder', f.label)
    return cls


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
            cleaned_data['start_time'] = datetime.datetime.now()

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
    state = forms.ChoiceField(choices=STATES)


class StopwatchForm(forms.Form):
    start_time = forms.FloatField()
    dnf = forms.BooleanField(required=False, label='DNF')
    durations = DurationListField(
        required=False,
        widget=forms.Textarea(attrs={'rows': '5', 'cols': '20'}))

    residue = forms.CharField(required=False)
    comment = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance')
        kwargs['initial']['durations'] = list(instance.leg_set.all())
        super(StopwatchForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(StopwatchForm, self).clean()
        if cleaned_data['dnf']:
            cleaned_data['result'] = 'dnf'
        else:
            cleaned_data['result'] = 'f'
        start_time = cleaned_data['start_time']
        if start_time < 0:
            start_time += 2 ** 32
        cleaned_data['start_time'] = to_current_timezone(
            datetime.datetime.fromtimestamp(start_time))
        return cleaned_data
