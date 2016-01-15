from __future__ import absolute_import, unicode_literals, division

from django.conf.urls import url

from stopwatch.views import (
    Json,
    TimeTrialCreate, TimeTrialDetail, TimeTrialList, TimeTrialBest,
    TimeTrialAllBest, TimeTrialStopwatch, TimeTrialUpdate,
    TimeTrialStopwatchCreate, TimeTrialStopwatchLive, TimeTrialLiveUpdate,
)

urlpatterns = [
    url(r'^$', TimeTrialList.as_view(),
        name='timetrial_list'),
    url(r'^json/$', Json.as_view(),
        name='timetrial_json'),
    url(r'^best/$', TimeTrialAllBest.as_view(),
        name='timetrial_best', kwargs={'season': 'alltime'}),
    url(r'^best/(?P<legs>\d+)/$', TimeTrialBest.as_view(),
        name='timetrial_best_legs', kwargs={'season': 'alltime'}),
    url(r'^best/current/$', TimeTrialAllBest.as_view(),
        name='timetrial_best_current', kwargs={'season': 'current'}),
    url(r'^best/current/(?P<legs>\d+)/$', TimeTrialBest.as_view(),
        name='timetrial_best_legs_current', kwargs={'season': 'current'}),
    url(r'^create/$', TimeTrialCreate.as_view(),
        name='timetrial_create'),
    url(r'^(?P<pk>\d+)/$', TimeTrialDetail.as_view(),
        name='timetrial_detail'),
    url(r'^(?P<pk>\d+)/edit/$', TimeTrialUpdate.as_view(),
        name='timetrial_update'),
    url(r'^(?P<pk>\d+)/live/$', TimeTrialStopwatchLive.as_view(),
        name='timetrial_live'),
    url(r'^(?P<pk>\d+)/liveupdate/$', TimeTrialLiveUpdate.as_view(),
        name='timetrial_liveupdate'),
    url(r'^stopwatch/$', TimeTrialStopwatchCreate.as_view(),
        name='timetrial_stopwatch_create'),
    url(r'^(?P<pk>\d+)/stopwatch/$', TimeTrialStopwatch.as_view(),
        name='timetrial_stopwatch'),
]
