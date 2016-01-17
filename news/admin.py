from __future__ import absolute_import, unicode_literals, division

from django.contrib import admin
from news.models import NewsProfile, Config, Post, Comment


admin.site.register(NewsProfile, admin.ModelAdmin)
admin.site.register(Config, admin.ModelAdmin)
admin.site.register(Post, admin.ModelAdmin)
admin.site.register(Comment, admin.ModelAdmin)
