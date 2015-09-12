# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.core.urlresolvers import reverse
from django.views.generic import ListView, CreateView

from iou.models import Expence, ExpenceProfile
from iou.forms import ExpenceCreateForm


class BalanceList(ListView):
    template_name = 'iou/balancelist.html'

    def get_queryset(self):
        return sorted(ExpenceProfile.all_named(),
                      key=lambda p: p.balance)


class ExpenceCreate(CreateView):
    template_name = 'iou/expencecreate.html'
    form_class = ExpenceCreateForm

    def get_profiles(self):
        return sorted(ExpenceProfile.all_named(),
                      key=lambda p: p.balance)

    def get_form_kwargs(self, **kwargs):
        kwargs = super(ExpenceCreate, self).get_form_kwargs(**kwargs)
        kwargs['profiles'] = self.get_profiles()
        return kwargs

    def get_success_url(self):
        return reverse('balance_list')


class ExpenceList(ListView):
    template_name = 'iou/expencelist.html'
    queryset = Expence.objects.all()
