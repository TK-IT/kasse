from __future__ import absolute_import, unicode_literals, division

import types
import functools

from django.utils.functional import SimpleLazyObject

from kasse.models import Profile


def get_profile(request):
    KEY = 'kasse_profile_id'
    u = request.user if request.user.is_authenticated() else None

    if KEY in request.session:
        try:
            return Profile.objects.get(
                pk=int(request.session[KEY]),
                user=u)
        except Profile.DoesNotExist:
            pass

    if u:
        try:
            return Profile.objects.get(user=u)
        except Profile.DoesNotExist:
            pass


def get_or_create_profile(request):
    if request.profile:
        return request.profile
    p = Profile()
    p.save()
    request.profile = p
    request.session['kasse_profile_id'] = p.pk
    return p


class Middleware(object):
    def process_request(self, request):
        request.profile = SimpleLazyObject(functools.partial(
            get_profile, request))
        request.get_or_create_profile = functools.partial(
            get_or_create_profile, request)
