from __future__ import absolute_import, unicode_literals, division

from django import template

from django.core.urlresolvers import reverse
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True, needs_autoescape=True)
def display_profile(profile, autoescape=True):
    if autoescape:
        profile = conditional_escape(profile)
    return mark_safe(
        '<a href="%s">%s</a>' % (
            reverse('home'),
            profile))


@register.filter
def display_duration(duration):
    minutes, seconds = divmod(duration, 60)
    return '%d:%05.2f' % (minutes, seconds)
