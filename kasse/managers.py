# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.db import models


class ProfileManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        qs = super(ProfileManager, self).get_queryset()
        return qs.select_related('association', 'title__association')
