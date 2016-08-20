# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import datetime
import itertools
import collections

from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from django.db.models import Q

from kasse.templatetags.kasse_extras import display_duration_plain


def frozendict(**kwargs):
    return collections.namedtuple('frozendict', kwargs.keys())(**kwargs)


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
    """Get a list of the recently active TimeTrials.

    Only consider TimeTrials that have been created recently.

    If two TimeTrials are recently active for the same profile,
    decide which to use based on timetrial_tiebreaker.

    If there was activity within the last moment, raise TryAgainShortly
    indicating how long to wait before reporting anything.

    The queryset may be a Django QuerySet or a news.test.PastTimeTrialQuerySet.
    """

    if now is None:
        now = timezone.now()

    threshold = datetime.timedelta(hours=12)
    qs = qs.exclude(Q(state='initial') & ~Q(result=''))
    qs = qs.exclude(profile__newsprofile__ignore=True)
    qs = qs.filter(created_time__gt=now - threshold)

    qs = qs.order_by('profile_id')
    qs_groups = itertools.groupby(qs, key=lambda tt: tt.profile_id)

    last_modified = now - threshold

    timetrials = []
    for profile_id, tts in qs_groups:
        tt = max(tts, key=timetrial_tiebreaker)

        if tt.result != '':
            pass
        elif tt.start_time != None and tt.state != 'initial':  # noqa
            last_modified = max(last_modified, tt.start_time)
        else:
            last_modified = max(last_modified, tt.created_time)
        timetrials.append(tt)

    age = (now - last_modified).total_seconds()
    grace_seconds = 5
    if age < grace_seconds:
        raise TryAgainShortly(grace_seconds - age)
    return timetrials


def tt_kasse_i_kass(timetrial):
    return timetrial.id == 335


def profile_kass(profile):
    return profile.id == 164


def get_timetrial_state(tt):
    """Returns a tuple (kind, args) indicating what to report."""

    if tt.result == '':
        if tt.state == 'initial' or tt.start_time == None:  # noqa
            return 'upcoming', frozendict()
        elif tt.leg_count >= 5 or tt_kasse_i_kass(tt):
            d = display_duration_plain(tt.duration)
            return 'time', frozendict(leg_count=tt.leg_count, time=d)
        else:
            return 'started', frozendict()
    else:
        d = display_duration_plain(tt.duration)
        args = frozendict(leg_count=tt.leg_count, time=d)
        if tt.result == 'f':
            return 'time', args
        elif tt.result == 'dnf':
            return 'dnf', args
        elif tt.result == 'irr':
            return 'irr', args
        else:
            return 'unknown', frozendict()


def iter_timetrial_comments(tt):
    if tt_kasse_i_kass(tt) and tt.start_time is not None:
        t = tt.start_time
        for i, leg in enumerate(tt.leg_set.all()):
            t += datetime.timedelta(seconds=leg.duration)
            yield ('kasstime', frozendict(i=i + 1, time=t))
    if tt.result != '' and tt.residue != None:  # noqa
        yield ('residue', frozendict(residue=tt.residue))
    if tt.result != '' and tt.comment:
        yield ('comment', frozendict(comment=tt.comment))
    for image in tt.image_set.all():
        yield ('attachment', frozendict(url=image.image.url))


def get_timetrial_comments(tt):
    return frozenset(iter_timetrial_comments(tt))


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


def describe_timetrial_state(profiles):
    """Given a dict of {profile: (st, args)},
    with (st, args) reported by get_timetrial_state,
    return a text describing the info without a "read more" URL.

    >>> def p(i): return frozendict(id=i)
    >>> print(describe_timetrial_state({
    ...     p(1): ('upcoming', frozendict()),
    ...     p(2): ('upcoming', frozendict()),
    ... }))
    frozendict(id=1) og frozendict(id=2) gør klar til at tage øl på tid.
    >>> print(describe_timetrial_state({
    ...     p(1): ('started', frozendict()),
    ...     p(2): ('started', frozendict()),
    ... }))
    frozendict(id=1) og frozendict(id=2) er begyndt at drikke!
    >>> print(describe_timetrial_state({
    ...     p(1): ('irr', frozendict(leg_count=3, time=42)),
    ...     p(2): ('started', frozendict()),
    ... }))
    frozendict(id=1) har drukket 3 øl på 42, men tiden er erklæret ugyldig.
    frozendict(id=2) er i gang med at drikke øl på tid.
    >>> print(describe_timetrial_state({
    ...     p(5): ('time', frozendict(leg_count=1, time=10)),
    ...     p(4): ('time', frozendict(leg_count=2, time=30)),
    ...     p(3): ('irr', frozendict(leg_count=3, time=60)),
    ...     p(2): ('time', frozendict(leg_count=4, time=100)),
    ...     p(1): ('dnf', frozendict(leg_count=5, time=150)),
    ...     p(6): ('started', frozendict()),
    ...     p(7): ('started', frozendict()),
    ...     p(8): ('upcoming', frozendict()),
    ... }))
    Tiderne blev:
    * frozendict(id=5): 1 øl på 10.
    * frozendict(id=4): 2 øl på 30.
    * frozendict(id=3): 3 øl på 60, men tiden er erklæret ugyldig.
    * frozendict(id=2): 4 øl på 100.
    * frozendict(id=1): DNF efter 5 øl på 150.
    frozendict(id=6) og frozendict(id=7) er i gang med at drikke øl på tid.
    frozendict(id=8) gør klar til at tage øl på tid.
    """

    groups = {}
    for profile, (st, args) in profiles.items():
        # st may be "unknown", which we silently ignore
        groups.setdefault(st, []).append((profile, args))

    tpl = {
        'upcoming+': '%s gør klar til at tage øl på tid.',
        'started+': '%s er begyndt at drikke!',
        'continues+': '%s er i gang med at drikke øl på tid.',
        'time1': '%(profile)s har drukket %(leg_count)s øl på %(time)s',
        'dnf':
        '%(profile)s har lavet en DNF efter %(leg_count)s øl på %(time)s.',
        'irr': '%(profile)s har drukket %(leg_count)s øl på %(time)s, ' +
               'men tiden er erklæret ugyldig.',
    }

    texts = []
    done_tpl = {
        'time': '* %(profile)s: %(leg_count)s øl på %(time)s.',
        'dnf': '* %(profile)s: DNF efter %(leg_count)s øl på %(time)s.',
        'irr': '* %(profile)s: %(leg_count)s øl på %(time)s, ' +
               'men tiden er erklæret ugyldig.',
    }
    done = [(k, profile, args)
            for k in done_tpl.keys()
            for profile, args in groups.get(k, [])]
    list_mode = False
    if len(done) >= 4:
        list_mode = True
        done.sort(key=lambda v: v[2].time)
        texts.append("Tiderne blev:")
        for k, profile, args in done:
            texts.append(done_tpl[k] % dict(profile=profile, **args._asdict()))
    for key in 'time irr dnf started upcoming'.split():
        if list_mode and key in done_tpl.keys():
            continue
        try:
            values = groups[key]
        except KeyError:
            continue
        values.sort(key=lambda v: v[0].id)
        profiles = [profile for profile, args in values]
        values = [(v[0],) + tuple(v[1:]) for v in values]
        if key == 'started' and done:
            key = 'continues'
        if ('%s1' % key) in tpl:
            t = tpl['%s1' % key]
            parts = []
            for v in values:
                parts.append(t % dict(profile=v[0], **v[1]._asdict()))
            texts.append(join_parts(parts, ucfirst=(t[0] != '%')))
        elif ('%s+' % key) in tpl:
            texts.append(tpl['%s+' % key] % join_names(profiles))
        elif key in tpl:
            for v in values:
                texts.append(tpl[key] % dict(profile=v[0], **v[1]._asdict()))

    return '\n'.join(texts)


def comment_to_string(profile, comment):
    kind, args = comment
    args = args._asdict()
    for k in args:
        if isinstance(args[k], datetime.datetime):
            args[k] = timezone.localtime(args[k]).strftime('%H:%M')
    tpl = {
        'kasstime': '%(time)s: %(profile)s har drukket den %(i)s. øl.',
        'residue': '%(profile)ss rest var %(residue)g cL.',
        'comment': '%(profile)ss kommentar: "%(comment)s".',
    }
    return tpl[kind] % dict(profile=profile, **args)


def info_links(tts):
    pks = sorted(tt.id for tt in tts)
    return (
        'Følg med: %s' %
        ', '.join('https://tket.dk/5/%d' % i for i in pks))


def reconstruct_state(timetrials):
    """
    timetrials[tt] == post means tt is associated with post.

    >>> from kasse.models import Profile
    >>> p1, p2, p3 = Profile(pk=1), Profile(pk=2), Profile(pk=3)
    >>> tt1 = TimeTrial(profile=p1), tt2 = TimeTrial(profile=p2)
    >>> tt3 = TimeTrial(profile=p3)
    >>> st = reconstruct_state({tt1: 'a', tt2: 'a', tt3: 'b'})
    >>> sorted(st)
    ['a', 'b']
    >>> set(st['a']), set(st['b']) == set([p1, p2]), set([p3])
    True
    >>> st['a'][p1][0] == tt1
    True
    """
    posts = set(timetrials.values())
    return {post: {tt.profile: (tt, None, [])
                   if post == post_
                   for tt, post_ in timetrials.items()}
            for post in posts}


def update_report(delivery, state, current_events, logger):
    """
    Given a delivery agent, a state, and the latest CurrentEvents,
    report to the delivery agent and return the new state.

    state is a dict of {post: {profile: (tt, st, comments)}},
    where post is a post, profile is a profile, tt is a TimeTrial,
    st is a state as reported by get_timetrial_state, comments
    is a set of comments as reported by get_timetrial_comments.

    The delivery agent must support the three methods:
    - new_post(text), returning a post object
    - comment_on_post(post, text, attachment), returning a comment object
    - edit_post(text)
    where the post objects and comment objects may be of any hashable type.
    See implementations news.daemon.FacebookDelivery
    and news.test.TestDelivery.
    """

    if state is None:
        state = dict()

    try:
        # Find an existing post where all states are "upcoming".
        upcoming_post = next(
            post
            for post, profiles in state.items()
            if all(st[0] == 'upcoming'
                   for profile, (tt, st, comments) in profiles.items())
        )
    except StopIteration:
        upcoming_post = None

    # If profile_posts[profile] == post, then profile is a key in state[post].
    profile_posts = {
        profile: post
        for post, profiles in state.items()
        for profile in profiles.keys()
    }

    new_state = dict()
    for tt in current_events:
        profile = tt.profile
        k = profile_posts.get(profile, upcoming_post)
        if k not in new_state:
            new_state[k] = {
                profile: stuff
                for profile, stuff in state.get(k, dict()).items()
            }
        new_state[k][profile] = (
            tt, get_timetrial_state(tt), get_timetrial_comments(tt))

    the_new_post = None

    def get_post_comments(profiles):
        return set(
            (profile, comment)
            for profile, (tt, st, comments) in profiles.items()
            for comment in comments
        )

    def get_post_state(profiles):
        return {
            profile: st
            for profile, (tt, st, comments) in profiles.items()
        }

    def post_state_repr(post_state):
        return "dict(%s)" % ', '.join(
            '%d=%r' % (profile.id, stuff)
            for profile, stuff in post_state.items()
        )

    for post, profiles in new_state.items():
        if post is None and len(profiles) == 1:
            (tt, st, comments), = profiles.values()
            if st[0] == 'upcoming' and not tt_kasse_i_kass(tt):
                # Only a single upcoming TimeTrial -- don't create this post
                continue

        prev_profiles = state.get(post, dict())
        prev_comments = get_post_comments(prev_profiles)
        cur_comments = get_post_comments(profiles)
        new_comments = sorted(cur_comments - prev_comments, key=str)

        prev_post_state = get_post_state(prev_profiles)
        cur_post_state = get_post_state(profiles)
        if prev_post_state != cur_post_state:
            post_text = describe_timetrial_state(cur_post_state)
            tts = [tt for profile, (tt, st, comments) in profiles.items()]
            post_links = info_links(tts)
            if post_links:
                post_text += '\n' + post_links

            if post is None:
                the_new_post = post = delivery.new_post(post_text, tts)
                logger.info(
                    "New post %s: %s",
                    the_new_post, post_state_repr(cur_post_state))
            else:
                delivery.edit_post(post, post_text, tts)
                logger.info(
                    "Edit post %s: %s",
                    post, post_state_repr(cur_post_state))

        if new_comments:
            attachments = []
            comment_texts = []
            for profile, (kind, args) in new_comments:
                if kind == 'attachment':
                    attachments.append((profile, args.url))
                else:
                    comment_texts.append(
                        comment_to_string(profile, (kind, args)))
            comment_text = '\n'.join(comment_texts)
            attachment = attachments[0][1] if attachments else None
            comment = delivery.comment_on_post(post, comment_text, attachment)
            logger.info("Comment %s: %r attachment=%r",
                        comment, new_comments, attachment)
            for profile, url in attachments[1:]:
                comment = delivery.comment_on_post(
                    post, "%s har tilføjet et billede." % profile, url)
                logger.info("Attachment comment %s: %r", comment, url)

    if the_new_post is not None:
        new_state[the_new_post] = new_state.pop(None)
    else:
        new_state.pop(None, None)
    return new_state
