from __future__ import absolute_import, unicode_literals, division

from django.contrib import admin
from kasse.models import Association, Title, Profile, Contest


class TitleAdmin(admin.ModelAdmin):
    list_select_related = ('association', 'profile')
    list_display = (
        '__str__', 'association', 'profile',
    )


class AnonymousFilter(admin.SimpleListFilter):
    title = 'anonym'
    parameter_name = 'anonymous'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'anonym'),
            ('no', 'ej anonym'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            queryset = queryset.filter(name='', title__isnull=True)
        elif self.value() == 'no':
            queryset = queryset.exclude(name='', title__isnull=True)
        return queryset


class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'get_profile_display', 'title', 'name', 'get_anonymous',
    )

    list_filter = (AnonymousFilter, 'association')

    def get_profile_display(self, o):
        return str(o)
    get_profile_display.short_description = 'Profile'
    get_profile_display.admin_order_field = 'display_name'


admin.site.register(Association)
admin.site.register(Title, TitleAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Contest)
