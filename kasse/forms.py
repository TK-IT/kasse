# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.core.exceptions import ValidationError
from django import forms
from django.utils import six
from django.contrib.auth.forms import UserCreationForm as AdminUserCreationForm

from kasse.models import Profile, Association
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


@label_placeholder
class ProfileCreateForm(forms.Form):
    name = forms.CharField(required=False, label='Navn')
    title = forms.CharField(required=False, label='Titel')
    period = forms.IntegerField(required=False, label='Periode')
    association = AssociationModelChoiceField(required=False)

    def clean(self):
        cleaned_data = super(ProfileCreateForm, self).clean()
        name = cleaned_data['name']
        title = cleaned_data['title']
        association = cleaned_data['association']
        if not name and not title:
            self.add_error('name', 'Navn er påkrævet.')
        if title and not association:
            self.add_error('association', 'Titel kræver en tilknytning.')

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
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['name', 'favorite_drink', 'association']

    title = forms.CharField(required=False, label='Titel')
    association = forms.ModelChoiceField(
        Association.objects.all(), required=False,
        empty_label=Association.none_string(), label='Tilknytning')
    period = forms.CharField(required=False, label='Periode')

    def set_period_field(self, association):
        self.fields['period'] = forms.CharField(required=False)
        if association is not None:
            if association.name == 'TÅGEKAMMERET':
                self.fields['period'] = TKPeriodField(required=False)
            elif association.name == '@lkymia':
                self.fields['period'] = APeriodField(required=False)

    def clean_association(self):
        a = self.cleaned_data['association']
        self.set_period_field(a)
        self.did_clean_association = True
        return a

    def clean_period(self):
        if not self.did_clean_association:
            raise ValidationError("Cleaned fields in the wrong order")
        p = self.cleaned_data['period']
        p = self.fields['period'].clean(p)
        if p is None:
            return p
        if not isinstance(p, six.integer_types):
            raise ValidationError("Period is %r, not an int; field is %s" %
                (p, type(self.fields['period'])))
        return p

    def clean(self):
        self.did_clean_association = False
        cleaned_data = super(ProfileEditForm, self).clean()
        association = cleaned_data.get('association')
        period = cleaned_data.get('period')
        if cleaned_data.get('title'):
            if 'association' in cleaned_data and not association:
                self.add_error(
                    'association',
                    'Tilknytning er påkrævet når titel er oplyst')
        elif 'period' in cleaned_data and period is not None:
            self.add_error('title', 'Titel er påkrævet når periode er oplyst')
        return cleaned_data

    def __init__(self, *args, **kwargs):
        instance = kwargs['instance']
        if instance.title:
            kwargs['initial']['title'] = instance.title.title
            kwargs['initial']['period'] = instance.title.period
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        if not self.is_bound:
            self.set_period_field(instance.association)

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
