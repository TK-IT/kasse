from __future__ import absolute_import, unicode_literals, division

from django import template

from django.core.urlresolvers import reverse
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True, needs_autoescape=True)
def display_profile(profile, autoescape=True):
    association = profile.get_association_display()
    # profile_id = profile.pk
    if autoescape:
        profile = conditional_escape(profile)
    # return mark_safe(
    #     '<a href="%s" title="%s">%s</a>' % (
    #         reverse('profile', kwargs={'pk': profile_id}),
    #         association,
    #         profile))
    return mark_safe(
        '<span title="%s">%s</span>' % (
            association,
            profile))


@register.filter(is_safe=True, needs_autoescape=True)
def display_profile_plain(profile, autoescape=True):
    if autoescape:
        profile = conditional_escape(profile)
    return mark_safe('%s' % (profile,))


@register.filter
def display_duration(duration):
    minutes, seconds = divmod(duration, 60)
    return '%d:%05.2f' % (minutes, seconds)
