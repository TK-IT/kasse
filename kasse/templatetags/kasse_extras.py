# vim:set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django import template

from django.core.urlresolvers import reverse
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True, needs_autoescape=True)
def display_profile(profile, autoescape=True):
    association = conditional_escape(profile.get_association_display())
    profile_id = profile.pk
    if autoescape:
        profile = conditional_escape(profile)
    return mark_safe(
        '<a href="%s" title="%s" class="profile_link">%s</a>' % (
            reverse('profile', kwargs={'pk': profile_id}),
            association,
            profile))


@register.filter(is_safe=True, needs_autoescape=True)
def display_profile_plain(profile, autoescape=True):
    if autoescape:
        profile = conditional_escape(profile)
    return mark_safe('%s' % (profile,))


@register.filter
def display_difference(duration):
    s = '%+.2f' % duration
    return s.replace('-', '−')
    # minutes, seconds = divmod(duration or 0, 60)
    # hours, minutes = divmod(minutes, 60)
    # if hours > 0:
    #     return '%d:%02d:%05.2f' % (hours, minutes, seconds)
    # else:
    #     return '%d:%05.2f' % (minutes, seconds)


@register.filter
def display_duration_plain(duration):
    minutes, seconds = divmod(duration or 0, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return '%d:%02d:%02.0f' % (hours, minutes, seconds)
    elif minutes >= 10:
        return '%d:%04.1f' % (minutes, seconds)
    else:
        return '%d:%05.2f' % (minutes, seconds)


@register.filter
def display_duration(duration):
    return display_duration_plain(duration)


@register.filter
def display_association(association):
    association = conditional_escape(association)
    return mark_safe('<span>%s</span>' % (association,))


@register.filter(is_safe=True, needs_autoescape=True)
def strip_space_after_tag(o, autoescape=True):
    if autoescape:
        s = conditional_escape(o)
    else:
        s = '%s' % (o,)
    return mark_safe(s.replace("> ", ">", 1))


@register.filter
def pct(value, arg):
    try:
        return '{0:.5g}'.format(value / arg * 100)
    except (ValueError, ZeroDivisionError):
        return None
