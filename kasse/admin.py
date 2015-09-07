from __future__ import absolute_import, unicode_literals, division

from django.contrib import admin
from kasse.models import Association, Title, Profile


admin.site.register(Association)
admin.site.register(Title)
admin.site.register(Profile)
