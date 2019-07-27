# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.urls import reverse
from django.views.generic import ListView, CreateView

from iou.models import Expence, ExpenceProfile
from iou.forms import ExpenceCreateForm


class BalanceList(ListView):
    template_name = 'iou/balancelist.html'

    def get_queryset(self):
        qs = ExpenceProfile.all_named()
        if self.request.association:
            qs = qs.filter(association=self.request.association)
        qs = [p for p in qs if p.balance]
        return sorted(qs, key=lambda p: p.balance)


class ExpenceCreate(CreateView):
    template_name = 'iou/expencecreate.html'
    form_class = ExpenceCreateForm

    def get_profiles(self):
        qs = ExpenceProfile.all_named()
        if self.request.association:
            qs = qs.filter(association=self.request.association)
        return sorted(qs, key=lambda p: p.balance)

    def get_form_kwargs(self, **kwargs):
        kwargs = super(ExpenceCreate, self).get_form_kwargs(**kwargs)
        kwargs['profiles'] = self.get_profiles()
        return kwargs

    def get_success_url(self):
        return reverse('balance_list')


class ExpenceList(ListView):
    template_name = 'iou/expencelist.html'

    def get_queryset(self):
        qs = Expence.objects.all()
        if self.request.association:
            qs = qs.filter(payer__association=self.request.association)
        return qs
