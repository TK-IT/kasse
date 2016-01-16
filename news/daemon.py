# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import os
import sys
import time
import codecs
import logging

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kasse.settings")

    import django

    django.setup()

from stopwatch.models import TimeTrial
from news.reporter import TryAgainShortly, get_current_events, update_report
from news.facebook import new_post, comment_on_latest_post


logger = logging.getLogger('news')


def main():
    qs = TimeTrial.objects.all()
    events = get_current_events(qs)
    report, action = update_report(None, events)

    while True:
        try:
            events = get_current_events(qs.all())
            sys.stdout.write(unicode(events).encode('ascii', errors='replace'))
            sys.stdout.write('\n')
            report, action = update_report(report, events)
        except TryAgainShortly as e:
            logger.debug("Try again in %s", e.suggested_wait)
            time.sleep(e.suggested_wait)
            continue
        if action != None:  # noqa
            action, text = action
            if action == 'new':
                p = new_post(text)
            elif action == 'comment':
                p = comment_on_latest_post(text)
            logger.debug("%s", p)
        time.sleep(15)


if __name__ == "__main__":
    main()
