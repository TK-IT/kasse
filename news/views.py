from __future__ import absolute_import, unicode_literals, division

import datetime
import requests

from django.utils import timezone
from django.views.generic import View
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from news.models import Config


class FacebookLogin(View):
    @staticmethod
    def get_redirect_uri():
        redirect_uri = (
            'https://enkasseienfestforening.dk' +
            reverse('news_login_callback'))
        return redirect_uri

    def get(self, request):
        c = Config.objects.get()
        return HttpResponseRedirect(
            "https://www.facebook.com/dialog/oauth" +
            "?client_id=%s" % c.client_id +
            "&redirect_uri=%s" % self.get_redirect_uri() +
            "&response_type=code&scope=manage_pages,publish_pages")


class FacebookLoginCallback(View):
    def get(self, request):
        if request.GET.get('error'):
            return HttpResponse("You cancelled!")

        c = Config.objects.get()
        client_id = c.client_id
        app_secret = c.app_secret
        redirect_uri = FacebookLogin.get_redirect_uri()
        code = request.GET['code']
        # We have a code. We must exchange it for a user access token
        r = requests.get(
            "https://graph.facebook.com/v2.3/oauth/access_token" +
            "?client_id=%s" % client_id +
            "&redirect_uri=%s" % redirect_uri +
            "&client_secret=%s" % app_secret +
            "&code=%s" % code)
        o = r.json()
        try:
            user_access_token = o['access_token']
        except KeyError:
            o['kassenews'] = 1
            return JsonResponse(o)
        # token_type = o['token_type']
        seconds = o['expires_in']
        expiry = timezone.now() + datetime.timedelta(seconds=seconds)

        app_access_token = requests.get(
            "https://graph.facebook.com/oauth/access_token" +
            "?client_id=%s" % client_id +
            "&client_secret=%s" % app_secret +
            "&grant_type=client_credentials").text
        if not app_access_token.startswith('access_token='):
            return HttpResponse(
                "Not an access token:\n%s" % (app_access_token,),
                content_type='text/plain; charset=utf8')
        app_access_token = app_access_token[len('access_token='):]
        token_test = requests.get(
            "https://graph.facebook.com/debug_token" +
            "?input_token=%s" % user_access_token +
            "&access_token=%s" % app_access_token).json()
        if 'data' not in token_test:
            return JsonResponse(token_test)

        user_pages = requests.get(
            "https://graph.facebook.com/me/accounts" +
            "?access_token=%s" % user_access_token).json()
        if 'data' not in user_pages:
            return JsonResponse(user_pages)
        page_id = '536317743199338'
        try:
            page = next(o for o in user_pages['data']
                        if o['id'] == page_id)
        except StopIteration:
            return HttpResponse(
                "User cannot manage %s" % page_id)
        page_access_token = page['access_token']
        token_test = requests.get(
            "https://graph.facebook.com/debug_token" +
            "?input_token=%s" % page_access_token +
            "&access_token=%s" % app_access_token).json()
        if 'data' not in token_test:
            return JsonResponse(token_test)

        Config.objects.all().update(
            user_access_token=user_access_token,
            user_access_token_expiry=expiry,
            page_access_token=page_access_token,
        )
        return HttpResponse("All set!")
