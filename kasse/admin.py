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
        'get_profile_display', 'get_anonymous',
    )

    def get_profile_display(self, o):
        return str(o)
    get_profile_display.short_description = 'Profile'
    get_profile_display.admin_order_field = 'display_name'


admin.site.register(Association)
admin.site.register(Title, TitleAdmin)
admin.site.register(Profile, ProfileAdmin)
