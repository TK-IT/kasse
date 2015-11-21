from __future__ import absolute_import, unicode_literals, division

from django.contrib import admin
from iou.models import ExpenceProfile, Expence


class ExpenceAdmin(admin.ModelAdmin):
    list_display = ('payer', 'amount', 'comment')
    list_select_related = ('payer',)


class ExpenceProfileAdmin(admin.ModelAdmin):
    pass


admin.site.register(Expence, ExpenceAdmin)
admin.site.register(ExpenceProfile, ExpenceProfileAdmin)
