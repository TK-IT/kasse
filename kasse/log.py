from __future__ import unicode_literals, absolute_import

import re
import logging


logger = logging.getLogger('kasse')


class AllowedHosts(logging.Filter):
    def filter(self, record):
        if record.name != 'django.security.DisallowedHost':
            return True
        msg_pattern = r"^Invalid HTTP_HOST header: '(\S+)'\. .*"
        mo = re.match(msg_pattern, record.msg)
        if mo is None:
            logger.info("Couldn't parse %r", record.msg, extra=dict(ip=None))
            return True
        host = mo.group(1)
        ip_pattern = r'^\d+\.\d+\.\d+\.\d+$'
        if re.match(ip_pattern, host):
            return False
        return True
