from __future__ import absolute_import, unicode_literals, division

from django.contrib import admin
from stopwatch.models import TimeTrial, Leg, Beverage


class TimeTrialStateFilter(admin.SimpleListFilter):
    title = 'state'
    parameter_name = 'state'

    def lookups(self, request, model_admin):
        return TimeTrial.RESULTS + TimeTrial.STATES

    def queryset(self, request, queryset):
        results = [f for f, l in TimeTrial.RESULTS]
        states = [f for f, l in TimeTrial.STATES]
        if self.value() in results:
            return queryset.filter(result=self.value())
        elif self.value() in states:
            return queryset.filter(result='', state=self.value())


class TimeTrialLegCountFilter(admin.SimpleListFilter):
    title = 'leg count'
    parameter_name = 'leg_count'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        qs = qs.values_list('leg_count', flat=True).distinct()
        counts = sorted(set(qs))
        return [(str(c), str(c)) for c in counts]

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(leg_count__exact=int(self.value()))


class TimeTrialAdmin(admin.ModelAdmin):
    list_filter = (
        TimeTrialStateFilter,
        TimeTrialLegCountFilter,
    )
    list_display = (
        'get_duration', 'get_leg_count', 'profile', 'result', 'state',
        'beverage', 'residue',
        'start_time', 'creator', 'created_time',
    )

    def get_duration(self, o):
        return o.get_duration_display()
    get_duration.short_description = 'Duration'
    get_duration.admin_order_field = 'duration'

    def get_leg_count(self, o):
        return o.leg_count
    get_leg_count.short_description = 'Leg count'
    get_leg_count.admin_order_field = 'leg_count'


class LegAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'timetrial', 'order', 'duration')
    list_select_related = ('timetrial',)

    def get_name(self, o):
        return '%s.%s %s' % (o.timetrial_id, o.order, o.duration)
    get_name.short_description = 'Leg'


admin.site.register(TimeTrial, TimeTrialAdmin)
admin.site.register(Leg, LegAdmin)
admin.site.register(Beverage, admin.ModelAdmin)
