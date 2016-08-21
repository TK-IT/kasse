# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import os
import time
import logging

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kasse.settings")

    import django

    django.setup()

from stopwatch.models import TimeTrial
from news.reporter import (
    TryAgainShortly, get_current_events, update_report,
    reconstruct_state,
)
from news.facebook import new_post, comment_on_post, edit_post


logger = logging.getLogger('news')


def get_current_events_wait():
    while True:
        try:
            events = get_current_events(TimeTrial.objects.all())
        except TryAgainShortly as e:
            logger.debug("Try again in %s", e.suggested_wait)
            time.sleep(e.suggested_wait)
            continue
        return events


def main():
    delivery = FacebookDelivery()
    events = get_current_events_wait()
    state = reconstruct_state(events)
    state = update_report(delivery, state, events, logger)

    while True:
        events = get_current_events_wait()
        state = update_report(delivery, state, events, logger)
        time.sleep(15)


class FacebookDelivery(object):
    def new_post(self, text, timetrials):
        post = new_post(text)
        post.timetrials.set(timetrials)
        return post

    def comment_on_post(self, post, text, attachment):
        attachment = None  # Facebook seems to dislike our photos
        return comment_on_post(post, text, attachment=attachment)

    def edit_post(self, post, text, timetrials):
        edit_post(post, text)
        post.timetrials.set(timetrials)


if __name__ == "__main__":
    main()
