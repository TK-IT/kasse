from __future__ import absolute_import, unicode_literals, division

from django.contrib import admin
from kasse.models import Association, Title, Profile


class TitleAdmin(admin.ModelAdmin):
    list_select_related = ('association', 'profile')
    list_display = (
        '__str__', 'association', 'profile',
    )


class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'is_anonymous',
    )

    def is_anonymous(self, o):
        return o.is_anonymous
    is_anonymous.boolean = True


admin.site.register(Association)
admin.site.register(Title, TitleAdmin)
admin.site.register(Profile, ProfileAdmin)
