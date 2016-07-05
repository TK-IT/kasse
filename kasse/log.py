from __future__ import unicode_literals, absolute_import

import re
import logging


logger = logging.getLogger('kasse')


class AllowedHosts(logging.Filter):
    def filter(self, record):
        if record.name != 'django.security.DisallowedHost':
            return True
        return False
