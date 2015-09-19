# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django import forms
from django.contrib.auth.forms import UserCreationForm as AdminUserCreationForm

from kasse.models import Profile, Association


def label_placeholder(cls):
    for f in cls.base_fields.values():
        f.widget.attrs.setdefault('placeholder', f.label)
    return cls


@label_placeholder
class LoginForm(forms.Form):
    profile = forms.ModelChoiceField(
        Profile.all_named(),
        empty_label="Brugernavn")
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False)
    next = forms.CharField(widget=forms.HiddenInput)


@label_placeholder
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
    period = forms.IntegerField(required=False, label='Periode')
    association = forms.ModelChoiceField(
        Association.objects.all(), required=False,
        empty_label=Association.none_string(), label='Tilknytning')

    def clean(self):
        cleaned_data = super(ProfileEditForm, self).clean()
        association = cleaned_data['association']
        period = cleaned_data['period']
        if cleaned_data['title']:
            if not association:
                self.add_error(
                    'association',
                    'Tilknytning er påkrævet når titel er oplyst')
        elif period is not None:
            self.add_error('title', 'Titel er påkrævet når periode er oplyst')
        if period and period < 1956 and association.name == 'TÅGEKAMMERET':
            self.add_error('period', 'Periode skal være et 4-cifret årstal')
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
