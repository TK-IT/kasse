from __future__ import absolute_import, unicode_literals, division

import functools

from django.utils.functional import SimpleLazyObject

from ipware.ip import get_real_ip

from kasse.models import Profile, Association


def get_profile(request):
    KEY = 'kasse_profile_id'
    u = request.user if request.user.is_authenticated else None

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


def filter_association(request, qs):
    KEY = 'kasse_association_id'
    a_id = request.session.get(KEY)
    if a_id is None:
        return qs
    if qs.model.__name__ == 'TimeTrial':
        return qs.filter(profile__association_id=a_id)
    else:
        raise Exception("Don't know how to handle %s" % (qs.model))


def Middleware(get_response):
    def process_request(request):
        request.profile = SimpleLazyObject(functools.partial(
            get_profile, request))
        request.get_or_create_profile = functools.partial(
            get_or_create_profile, request)
        request.log_data = {'ip': get_real_ip(request)}
        request.association = SimpleLazyObject(functools.partial(
            get_association, request))
        request.set_association = functools.partial(
            set_association, request)
        request.filter_association = functools.partial(
            filter_association, request)
        return get_response(request)

    return process_request
