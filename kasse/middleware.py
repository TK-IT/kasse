from __future__ import absolute_import, unicode_literals, division

import functools

from django.utils.functional import SimpleLazyObject

from ipware.ip import get_real_ip

from kasse.models import Profile, Association


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


def get_association(request):
    KEY = 'kasse_association_id'
    a_id = request.session.get(KEY)
    if a_id is None:
        return None
    try:
        a = Association.objects.get(pk=a_id)
    except Association.DoesNotExist:
        return None
    return a


def set_association(request, association):
    KEY = 'kasse_association_id'
    if association is None:
        try:
            del request.session[KEY]
        except KeyError:
            pass
    else:
        request.session[KEY] = association.pk


class Middleware(object):
    def process_request(self, request):
        request.profile = SimpleLazyObject(functools.partial(
            get_profile, request))
        request.get_or_create_profile = functools.partial(
            get_or_create_profile, request)
        request.log_data = {'ip': get_real_ip(request)}
        request.association = SimpleLazyObject(functools.partial(
            get_association, request))
        request.set_association = functools.partial(
            set_association, request)
