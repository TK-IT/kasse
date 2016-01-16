from __future__ import absolute_import, unicode_literals, division

from django.conf.urls import url

from news.views import FacebookLogin, FacebookLoginCallback

urlpatterns = [
    url(r'^login/$', FacebookLogin.as_view(),
        name='news_login'),
    url(r'^callback/$', FacebookLoginCallback.as_view(),
        name='news_login_callback'),
]
