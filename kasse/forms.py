# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.core.exceptions import ValidationError
from django import forms
from django.utils import six, timezone
from django.utils.dateparse import parse_duration
from django.contrib.auth.forms import UserCreationForm as AdminUserCreationForm

from kasse.models import Profile, Association, Contest
from kasse.fields import TKPeriodField, APeriodField


class ProfileModelChoiceField(forms.ModelChoiceField):
    def __init__(self, **kwargs):
        qs = Profile.all_named()
        qs = qs.order_by('-association', 'display_name')
        kwargs.setdefault('queryset', qs)
        super(ProfileModelChoiceField, self).__init__(**kwargs)

    def label_from_instance(self, obj):
        if obj.is_anonymous:
            return '%s' % (obj,)
        elif obj.association:
            return '%s (%s)' % (obj, obj.association)
        else:
            return '%s (independent)' % (obj,)


class AssociationModelChoiceField(forms.ModelChoiceField):
    def __init__(self, **kwargs):
        kwargs.setdefault('queryset', Association.objects.all())
        kwargs.setdefault('empty_label', Association.none_string())
        kwargs.setdefault('label', 'Tilknytning')
        super(AssociationModelChoiceField, self).__init__(**kwargs)


def label_placeholder(cls):
    for f in cls.base_fields.values():
        f.widget.attrs.setdefault('placeholder', f.label)
    return cls


@label_placeholder
class LoginForm(forms.Form):
    profile = ProfileModelChoiceField(empty_label="Brugernavn")
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False)
    next = forms.CharField(widget=forms.HiddenInput)


class PeriodFieldMixin:
    def get_period_field(self, association):
        if association is not None:
            if association.name == 'TÅGEKAMMERET':
                return TKPeriodField(required=False)
            elif association.name == '@lkymia':
                return APeriodField(required=False)

    def clean_association(self):
        a = self.cleaned_data['association']
        self.did_clean_association = True
        return a

    def clean_period(self):
        if not self.did_clean_association:
            raise ValidationError("Cleaned fields in the wrong order")
        p = self.cleaned_data['period']
        field = self.get_period_field(self.cleaned_data['association'])
        if not field:
            return p
        p = field.clean(p)
        if p and not isinstance(p, six.integer_types):
            raise ValidationError(
                "Period is %r, not an int; field is %s" %
                (p, type(self.fields['period'])))
        return p


@label_placeholder
class ProfileCreateForm(forms.Form, PeriodFieldMixin):
    name = forms.CharField(required=False, label='Navn')
    title = forms.CharField(required=False, label='Titel')
    association = AssociationModelChoiceField(
        required=False, empty_label='Forening')
    period = forms.CharField(required=False, label='År/semester')

    def clean(self):
        self.did_clean_association = False
        cleaned_data = super(ProfileCreateForm, self).clean()

        association = cleaned_data.get('association')
        if cleaned_data.get('title'):
            if 'association' in cleaned_data and not association:
                self.add_error(
                    'association',
                    'Tilknytning er påkrævet når titel er oplyst')
        elif cleaned_data.get('period'):
            self.add_error('title', 'Titel er påkrævet når periode er oplyst')

        name = cleaned_data.get('name')
        title = cleaned_data.get('title')
        if not name and not title:
            self.add_error('name', 'Navn er påkrævet.')
        return cleaned_data

    def save(self, instance):
        instance.name = self.cleaned_data['name']
        instance.association = self.cleaned_data['association'] or None
        title = self.cleaned_data['title'] or ''
        period = self.cleaned_data['period'] or None
        instance.set_title(title, period)


@label_placeholder
class UserCreationForm(AdminUserCreationForm):
    pass


@label_placeholder
class ProfileEditForm(forms.ModelForm, PeriodFieldMixin):
    class Meta:
        model = Profile
        fields = ['name', 'favorite_drink', 'association']

    title = forms.CharField(required=False, label='Titel')
    association = AssociationModelChoiceField(
        required=False, empty_label='Forening')
    period = forms.CharField(required=False, label='Periode')

    def clean(self):
        self.did_clean_association = False
        cleaned_data = super(ProfileEditForm, self).clean()
        association = cleaned_data.get('association')
        if cleaned_data.get('title'):
            if 'association' in cleaned_data and not association:
                self.add_error(
                    'association',
                    'Tilknytning er påkrævet når titel er oplyst')
        elif cleaned_data.get('period'):
            self.add_error('title', 'Titel er påkrævet når periode er oplyst')
        return cleaned_data

    def __init__(self, *args, **kwargs):
        instance = kwargs['instance']
        if instance.title:
            kwargs['initial']['title'] = instance.title.title
            kwargs['initial']['period'] = instance.title.period
        super(ProfileEditForm, self).__init__(*args, **kwargs)

    def save(self):
        instance = super(ProfileEditForm, self).save(commit=False)
        instance.association = self.cleaned_data['association'] or None
        title = self.cleaned_data['title'] or ''
        period = self.cleaned_data['period'] or None
        instance.set_title(title, period)
        instance.save()
        return instance


class AssociationForm(forms.Form):
    association = AssociationModelChoiceField(
        required=False, empty_label='Alle')


class ProfileMergeForm(forms.Form):
    destination = ProfileModelChoiceField()


class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['event_time', 'tk', 'alkymia']

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {}).setdefault(
            'event_time', self.get_initial_event_time())
        super(ContestForm, self).__init__(*args, **kwargs)

    def get_initial_event_time(self):
        dt = timezone.localtime(timezone.now())
        return dt.replace(hour=17, minute=0, second=0, microsecond=0)

    def clean_tk(self):
        value = self.cleaned_data['tk']
        if value != 'DNF' and parse_duration(value) is None:
            raise ValidationError('Must enter "DNF" or valid duration')
        return value

    def clean_alkymia(self):
        value = self.cleaned_data['alkymia']
        if value != 'DNF' and parse_duration(value) is None:
            raise ValidationError('Must enter "DNF" or valid duration')
        return value


class AssociationPeriodForm(forms.Form):
    def __init__(self, **kwargs):
        self.titles = kwargs.pop('titles')
        profiles = kwargs.pop('profiles')
        super(AssociationPeriodForm, self).__init__(**kwargs)
        for key, label in self.titles:
            self.fields[key] = forms.ModelChoiceField(
                queryset=profiles, required=False, label=label)
