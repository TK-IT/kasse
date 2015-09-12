# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django import forms

from kasse.templatetags.kasse_extras import display_profile
from iou.models import Expence


class ExpenceCreateForm(forms.ModelForm):
    def __init__(self, profiles, **kwargs):
        super(ExpenceCreateForm, self).__init__(**kwargs)
        choices = [(p.pk, '') for p in profiles]
        self.fields['payer'] = forms.ChoiceField(
            choices=choices, widget=forms.RadioSelect)
        self.fields['consumers'] = forms.MultipleChoiceField(
            choices=choices, widget=forms.CheckboxSelectMultiple)
        self.profiles = [
            {'payer': payer, 'consumers': consumers, 'profile': p}
            for payer, consumers, p in
            zip(self['payer'], self['consumers'], profiles)
        ]
        self.profile_dict = {
            p.pk: p for p in profiles
        }

    def clean_payer(self):
        a = self.cleaned_data['payer']
        return self.profile_dict[int(a)]

    def clean_consumers(self):
        a = self.cleaned_data['consumers']
        return [self.profile_dict[int(b)] for b in a]

    class Meta:
        model = Expence
        fields = ['payer', 'consumers', 'amount', 'comment']
