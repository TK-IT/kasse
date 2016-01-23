# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import datetime
import itertools
import collections

from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone

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

    def profile_info(self, state, tt):
        if state == 'upcoming':
            yield ('upcoming', tt)
            return
        if state == 'done':
            d = display_duration_plain(tt.duration)
            if tt.result == 'f':
                yield ('time', tt, tt.leg_count, d)
            elif tt.result == 'dnf':
                yield ('dnf', tt, tt.leg_count, d)
        elif state == 'ongoing' and tt.leg_count >= 5:
            d = display_duration_plain(tt.duration)
            yield ('time', tt, tt.leg_count, d)
        else:
            assert state == 'ongoing' and tt.leg_count < 5
            yield ('started', tt)
        if state == 'done':
            if tt.residue != None:  # noqa
                yield ('residue', tt, tt.residue)
            if tt.comment:
                yield ('comment', tt, tt.comment)

    def info(self):
        for profile_id, (state, tt) in self.iterprofiles():
            for x in self.profile_info(state, tt):
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


def info_tiebreaker(info):
    """Tie breaker for info regarding the same profile:
    lower means more relevant/recent.
    Falsy means don't report."""

    prio = 'dnf time started upcoming'.split()
    try:
        return 1 + prio.index(info[0])
    except ValueError:
        return None


def info_tiebreak_filter(infos):
    def key(i):
        return i[1].profile

    return set(
        min(g, key=info_tiebreaker)
        for profile, g in itertools.groupby(sorted(infos, key=key), key=key)
    )


def split(f, s):
    t = set(filter(f, s))
    return t, s - t


def get_current_events(qs, now=None):
    """
    Only consider TimeTrials that have been created within the last hour.

    The current events are represented by a dict, mapping Profile pk
    to an event description.
    """

    if now is None:
        now = timezone.now()

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
        return '%s' % (profiles[0],)
    else:
        return '%s og %s' % (
            ', '.join('%s' % (p,) for p in profiles[:-1]), profiles[-1])


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


def describe_info(new_info):
    """Given a list of info as defined by CurrentEvents,
    return a text describing the info without a "read more" URL."""

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
        'continues+': '%s er i gang med at drikke øl på tid.',
        'time1': 'tiden for %s blev %s øl på %s',
        'dnf': '%s lavede en DNF: %s øl på %s.',
        'residue1': '%ss rest var %g cL',
        'comment': '%ss kommentar: "%s".',
    }

    texts = []
    started = []
    for key in 'time dnf residue comment started upcoming'.split():
        try:
            values = groups[key]
        except KeyError:
            continue
        values.sort(key=lambda v: v[0].profile.id)
        tts = [v[0] for v in values]
        profiles = [tt.profile for tt in tts]
        values = [(v[0].profile,) + tuple(v[1:]) for v in values]
        if key == 'started':
            started += tts
        if key == 'started' and ('time' in groups or 'dnf' in groups):
            key = 'continues'
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

    return '\n'.join(texts)


def info_links(new_info):
    pks = [i[1].id for i in new_info]
    pks = sorted(set(pks))
    return (
        'Følg med: %s' %
        ', '.join('http://tket.dk/5/%d' % i for i in pks))


def filter_info_set(info):
    if len(info) == 1:
        i = list(info)[0]
        if i[0] == 'upcoming':
            return set()
    return info


def update_report(delivery, state, current_events):
    """
    Given a delivery agent, a state, and the latest CurrentEvents,
    report to the delivery agent and return the new state.

    state is a dict of {post: (p, i)},
    where post is a post, p is a set of profiles, and i is a set of info.
    """

    if state is None:
        state = dict()

    try:
        upcoming_post = next(
            post
            for post, (profiles, infos) in state.items()
            if all(i[0] == 'upcoming' for i in infos)
        )
    except StopIteration:
        upcoming_post = None

    profile_posts = {
        profile: post
        for post, (profiles, infos) in state.items()
        for profile in profiles
    }

    new_state = dict()
    for i in current_events.info():
        profile = i[1].profile
        k = profile_posts.get(profile, upcoming_post)
        new_state.setdefault(k, (set(), set()))
        new_state[k][0].add(profile)
        new_state[k][1].add(i)

    the_new_post = None

    for post, (profiles, infos) in new_state.items():
        prev_profiles, prev_infos = state.get(post, (set(), set()))

        if post is None:
            if not filter_info_set(infos):
                continue

        post_info, comment_info = split(info_tiebreaker, infos)
        post_info = info_tiebreak_filter(post_info)
        p_post_info, p_comment_info = split(info_tiebreaker, prev_infos)
        p_post_info = info_tiebreak_filter(p_post_info)
        if post_info - p_post_info:
            post_info = info_tiebreak_filter(post_info)
            post_text = describe_info(post_info)
            post_links = info_links(post_info)
            if post_links:
                post_text += '\n' + post_links

            if post is None:
                the_new_post = delivery.new_post(post_text)
            else:
                delivery.edit_post(post, post_text)
        new_comments = comment_info - p_comment_info
        if new_comments:
            comment_text = describe_info(new_comments)
            delivery.comment_on_post(post, comment_text)

    if the_new_post is not None:
        new_state[the_new_post] = new_state.pop(None)
    else:
        new_state.pop(None, None)
    return new_state
