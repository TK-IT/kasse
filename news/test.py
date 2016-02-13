# vim: set fileencoding=utf8:
from __future__ import (
    absolute_import, unicode_literals, division, print_function)

import os
import sys
import codecs
import logging
import argparse
import datetime
import itertools

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kasse.settings")

    import django

    django.setup()

from stopwatch.models import TimeTrial  # noqa
from news.reporter import (  # noqa
    TryAgainShortly, get_current_events, update_report)


class TestDelivery(object):
    def __init__(self):
        self.comment_count = []

    def new_post(self, text, timetrials):
        self.comment_count.append(0)
        return len(self.comment_count)

    def comment_on_post(self, post, text, attachment):
        self.comment_count[post - 1] += 1
        return (post, self.comment_count[post - 1])

    def edit_post(self, post, text, timetrials):
        pass


class PastTimeTrialQuerySet:
    def __init__(self, now):
        self.qs = TimeTrial.objects.all()
        self.now = now

    def exclude(self, **kwargs):
        self.qs = self.qs.exclude(**kwargs)
        return self

    def filter(self, **kwargs):
        self.qs = self.qs.filter(**kwargs)
        return self

    def order_by(self, k):
        self.qs = self.qs.order_by(k)
        return self

    def __iter__(self):
        for tt in self.qs:
            if tt.created_time > self.now:
                continue
            fields = (
                'pk profile start_time created_time ' +
                'result state residue comment '
                '').split()
            kwargs = {f: getattr(tt, f) for f in fields}
            res = TimeTrial(**kwargs)
            legs = list(tt.leg_set.all())
            legs = [l for l in legs if l.time < self.now]
            res.leg_count = len(legs)
            res.duration = sum(l.duration for l in legs)
            if res.start_time > self.now:
                res.start_time = None
                res.leg_count = None
                res.duration = None
                res.result = ''
                res.state = 'initial'
            elif res.leg_count != tt.leg_count:
                res.result = ''
                res.state = 'running'
            yield res


def get_logger(output):
    logger = logging.getLogger('news.test')
    handlers = []
    handlers.append(logging.StreamHandler(None))
    if output:
        handlers.append(logging.FileHandler(output, 'a'))
    fmt = '[%(asctime)s %(levelname)s] %(message)s'
    datefmt = None
    formatter = logging.Formatter(fmt, datefmt)
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o')
    args = parser.parse_args()

    delivery = TestDelivery()
    logger = get_logger(args.output)

    my_print = logger.info

    created_times = TimeTrial.objects.filter(
        created_time__gte=datetime.date(2016, 1, 19))
    created_times = created_times.values_list('created_time', flat=True)
    created_times = sorted(created_times)
    created_times = [
        min(t)
        for _, t in itertools.groupby(created_times, key=lambda dt: dt.date())
    ]
    my_print("%s", created_times)
    sec = datetime.timedelta(seconds=1)
    state = None
    for t in created_times:
        stop = t + datetime.timedelta(days=1)
        stop = stop.replace(hour=0, minute=0, second=0)
        t = t - 7 * sec
        while t < stop:
            qs = PastTimeTrialQuerySet(t)
            delivery.now = t
            try:
                events = get_current_events(qs, t)
                state = update_report(delivery, state, events, logger)
            except TryAgainShortly as e:
                my_print("%s: %s", t, e)
                t += datetime.timedelta(seconds=e.suggested_wait + 1)
                continue
            t += 15 * sec


if __name__ == "__main__":
    main()
