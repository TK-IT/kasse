# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import datetime
import itertools
import collections

from django.utils.encoding import python_2_unicode_compatible

from kasse.templatetags.kasse_extras import display_duration_plain

from stopwatch.models import TimeTrial


CurrentEventsBase = collections.namedtuple(
    'CurrentEvents', 'done ongoing upcoming'.split())


@python_2_unicode_compatible
class CurrentEvents(CurrentEventsBase):
    def __str__(self):
        return "CurrentEvents(done=%s, ongoing=%s, upcoming=%s)" % tuple(
            "[%s]" % ', '.join("(%s, %s)" % x for x in y)
            for y in (self.done, self.ongoing, self.upcoming))

    def iterprofiles(self):
        for field in 'done ongoing upcoming'.split():
            for profile_id, tt in getattr(self, field):
                yield (profile_id, (field, tt))

    def profiles(self):
        try:
            return self._profiles
        except AttributeError:
            self._profiles = dict(self.iterprofiles())
            return self._profiles

    def profile_info(self, profile, state, tt):
        if state == 'upcoming':
            yield ('upcoming', profile)
            return
        if state == 'done':
            d = display_duration_plain(tt.duration)
            if tt.result == 'f':
                yield ('time', profile, tt.leg_count, d)
            elif tt.result == 'dnf':
                yield ('dnf', profile, tt.leg_count, d)
        elif state == 'ongoing' and tt.leg_count >= 5:
            d = display_duration_plain(tt.duration)
            yield ('time', profile, tt.leg_count, d)
        else:
            assert state == 'ongoing' and tt.leg_count < 5
            yield ('started', profile)
        if state == 'done':
            if tt.residue != None:  # noqa
                yield ('residue', profile, tt.residue)
            if tt.comment:
                yield ('comment', profile, tt.comment)

    def info(self):
        for profile_id, (state, tt) in self.iterprofiles():
            for x in self.profile_info(tt.profile, state, tt):
                yield x


@python_2_unicode_compatible
class TryAgainShortly(Exception):
    def __init__(self, suggested_wait):
        self.suggested_wait = suggested_wait

    def __str__(self):
        return "Try again in %s seconds" % self.suggested_wait


def timetrial_tiebreaker(tt):
    """Tie breaker for same-profile TimeTrials.

    Used by the news reporter to decide which is the "real" TimeTrial
    instance for a profile.
    """

    return (
        tt.result != '',  # Done is better
        tt.state != 'initial',  # Initiated is better
        tt.created_time,  # Created later is better
    )


def get_current_events(qs, now=None):
    """
    Only consider TimeTrials that have been created within the last hour.

    The current events are represented by a dict, mapping Profile pk
    to an event description.
    """

    if now is None:
        now = datetime.datetime.utcnow()

    # Hack to ensure that we are not mixing naive and aware datetimes
    tt_ = TimeTrial.objects.filter(start_time__isnull=False)[0]
    if tt_.start_time.tzinfo != now.tzinfo:
        # Assert that the database is in UTC
        assert unicode(tt_.start_time.tzinfo) == '<UTC>'
        # Assume that any argument 'now' was a naive UTC datetime
        now = now.replace(tzinfo=tt_.start_time.tzinfo)

    hour = datetime.timedelta(hours=1)
    qs = qs.exclude(result='f', state='initial')
    qs = qs.exclude(profile__newsprofile__ignore=True)
    qs = qs.filter(created_time__gt=now - hour)

    qs = qs.order_by('profile_id')
    qs_groups = itertools.groupby(qs, key=lambda tt: tt.profile_id)

    done = []
    ongoing = []
    upcoming = []
    for profile_id, tts in qs_groups:
        tt = max(tts, key=timetrial_tiebreaker)

        if tt.result != '':
            done.append((profile_id, tt))
        elif tt.start_time != None and tt.state != 'initial':  # noqa
            ongoing.append((profile_id, tt))
        else:
            upcoming.append((profile_id, tt))

    grace_period = 0

    if ongoing:
        ages = [
            (now - tt2.start_time).total_seconds()
            for _profile, tt2 in ongoing
        ]
        t = min(ages)
        grace_seconds = 5
        if t < grace_seconds:
            # A TimeTrial started within the last 5 seconds
            # It is unclear if the upcoming events are also starting now
            grace_period = max(grace_period, grace_seconds - t)
    if upcoming:
        ages = [
            (now - tt2.created_time).total_seconds()
            for _profile, tt2 in upcoming
        ]
        t = min(ages)
        grace_seconds = 5
        if t < grace_seconds:
            # A TimeTrial was created within the last 5 seconds
            # It is unclear if other events are upcoming
            grace_period = max(grace_period, grace_seconds - t)

    if grace_period > 0:
        raise TryAgainShortly(grace_period)

    res = CurrentEvents(done, ongoing, upcoming)
    return res


def join_names(profiles):
    if not profiles:
        return 'Ingen'
    if len(profiles) == 1:
        return unicode(profiles[0])
    else:
        return '%s og %s' % (
            ', '.join(map(unicode, profiles[:-1])), profiles[-1])


def join_parts(sentences, ucfirst):
    if len(sentences) == 0:
        return ''
    elif len(sentences) == 1:
        s = sentences[0]
    else:
        s = '%s, og %s' % (
            ', '.join(sentences[:-1]), sentences[-1])

    if ucfirst:
        s = s[0].upper() + s[1:]

    return s + '.'


def describe_info(current_events, new_info):
    groups = [('', [])]
    for x in new_info:
        if x[0] == groups[-1][0]:
            groups[-1][1].append(x[1:])
        else:
            groups.append((x[0], [x[1:]]))
    groups = groups[1:]  # Remove sentinel
    groups = dict(groups)

    tpl = {
        'upcoming+': '%s gør klar til at tage øl på tid.',
        'started+': '%s er begyndt at drikke!',
        'time1': 'tiden for %s blev %s øl på %s',
        'dnf': '%s lavede en DNF: %s øl på %s.',
        'residue1': '%ss rest var %s cL',
        'comment': '%ss kommentar: "%s".',
    }

    texts = []
    all_profiles = []
    started_profiles = []
    for key in 'time dnf residue comment started upcoming'.split():
        try:
            values = groups[key]
        except KeyError:
            continue
        profiles = [x[0] for x in values]
        all_profiles += profiles
        if key == 'started':
            started_profiles += profiles
        if ('%s1' % key) in tpl:
            t = tpl['%s1' % key]
            parts = []
            for v in values:
                parts.append(t % v)
            texts.append(join_parts(parts, ucfirst=(t[0] != '%')))
        elif ('%s+' % key) in tpl:
            texts.append(tpl['%s+' % key] % join_names(profiles))
        elif key in tpl:
            for v in values:
                texts.append(tpl[key] % v)

    all_profiles = set(all_profiles)
    if len(started_profiles) == 1:
        p = started_profiles[0].id
        tt = current_events.profiles()[p][1]
        texts.append('http://tket.dk/5/%d' % tt.id)
    elif len(started_profiles) > 1:
        ps = current_events.profiles()
        for p in started_profiles:
            tt = ps[p.id][1]
            texts.append('%s: http://tket.dk/5/%d' % (p, tt.id))
    elif len(all_profiles) == 1:
        p = list(all_profiles)[0].id
        tt = current_events.profiles()[p][1]
        texts.append('http://tket.dk/5/%d' % tt.id)
    else:
        texts.append('http://enkasseienfestforening.dk')

    return '\n'.join(texts)


def filter_info_set(info):
    if len(info) == 1:
        i = list(info)[0]
        if i[0] == 'upcoming':
            return set()
    return info


def update_report(previous_report, current_events, save=True):
    """
    Given the most recent report and the latest CurrentEvents,
    return a tuple (new_report, report_action)
    indicating the new "most recent report" and
    what reporting action should be taken.

    report_action will be a list of
    ("new", t), ("edit", p, t), ("comment", p, t)
    indicating that we should start a new report,
    edit Post p, comment on Post p, or do nothing.

    previous_report is a list of posts, each of which
    is a set of profiles and a list of infos.
    """

    if previous_report is None:
        previous_report = dict(), None, CurrentEvents([], [], [])
    prev_posts, prev_events = previous_report

    profiles = {
        profile.id: post
        for post in previous_posts
        for profile in post.profiles.all()
    }

    cur_info = filter_info_set(set(current_events.info()))
    cur_profiles = set(x[1].id for x in cur_info)
    prev_info = filter_info_set(set(previous_events.info()))
    prev_upcoming = set(i[1] for i in prev_info if i[0] == 'upcoming')
    prev_only_upcoming = all(i[0] == 'upcoming' for i in prev_info)
    new_info = sorted(cur_info - prev_info)
    new_profiles = set(x[1].id for x in cur_info) - set(profiles.keys())
    if prev_upcoming:
        post = profiles[next(iter(prev_upcoming)).id]
    else:
        post = None
    for profile in new_profiles:
        profiles.setdefault(profile.id, post)

    new_posts = []
    edits = dict()
    comments = dict()

    for v in new_info:
        if profiles[v[1].id]:
            post = profiles[v[1].id]
            comments.setdefault(post, []).append(v)
        else:
            new_posts.append(v)

    return (
        ([('new', describe_info(current_events, new_posts))]
         if new_posts else []) +
        [('edit', k, describe_info(current_events, v))
         for k, v in edits.items()] +
        [('comment', post, describe_info(current_events, v))
         for post, v in comments.items()])

    same_profiles = new_profiles & profiles.keys()
    if not new_info:
        return current_events, None
    text = describe_info(current_events, new_info)
    if same_profiles or (prev_info and prev_only_upcoming):
        return current_events, ('comment', text)
    else:
        return current_events, ('new', text)
