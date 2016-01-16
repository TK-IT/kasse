from __future__ import absolute_import, unicode_literals, division

from django.contrib import admin
from news.models import Config


admin.site.register(Config, admin.ModelAdmin)
