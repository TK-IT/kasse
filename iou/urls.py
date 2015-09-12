from __future__ import absolute_import, unicode_literals, division

from django.conf.urls import url

from iou.views import (
    BalanceList, ExpenceCreate, ExpenceList,
)

urlpatterns = [
    url(r'^balance/$', BalanceList.as_view(),
        name='balance_list'),
    url(r'^create/$', ExpenceCreate.as_view(),
        name='expence_create'),
    url(r'^$', ExpenceList.as_view(),
        name='expence_list'),
]
