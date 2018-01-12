# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import json
import logging
import datetime

from django.core.exceptions import FieldError, ValidationError
from django.core.urlresolvers import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.http import (
    HttpResponse, JsonResponse, HttpResponseRedirect,
    HttpResponseForbidden,
)
from django.views.defaults import permission_denied
from django.views.generic import (
    TemplateView, FormView, DetailView, ListView, UpdateView, View,
)
from django.views.generic.edit import BaseFormView
from django.forms.utils import to_current_timezone
from django.shortcuts import get_object_or_404

from stopwatch.forms import (
    TimeTrialCreateForm, TimeTrialForm,
    StopwatchForm, TimeTrialLiveForm,
)
from stopwatch.models import TimeTrial, Leg, Beverage, Image
from kasse.views import Home
from kasse.models import Profile, Title, Association

logger = logging.getLogger('kasse')


class TimeTrialCreate(FormView):
    form_class = TimeTrialCreateForm
    template_name = 'stopwatch/timetrialcreateform.html'

    def get_initial(self):
        initial = {'profile': self.request.profile}
        for k, v in self.request.GET.items():
            initial[k] = v
        try:
            initial['start_time'] = datetime.datetime.utcfromtimestamp(
                float(initial['start_time'])).replace(tzinfo=timezone.utc)
        except KeyError:
            # No initial start_time given
            pass
        except ValueError:
            # Given start_time is not formatted as a float
            pass
        try:
            initial['durations'] = '\n'.join(initial['durations'].split())
        except KeyError:
            pass
        return initial

    def get_context_data(self, **kwargs):
        context_data = super(TimeTrialCreate, self).get_context_data(**kwargs)
        if 'durations' in self.request.GET:
            context_data['has_initial'] = True
        return context_data

    def form_valid(self, form):
        data = form.cleaned_data
        now = timezone.now()
        stopwatch = False
        if data['individual_times'] == 'individual':
            durations = data['durations']
        elif data['individual_times'] == 'total':
            zero = datetime.timedelta(seconds=0)
            durations = [zero] * (data['legs'] - 1) + [data['total_time']]
        elif data['individual_times'] == 'stopwatch':
            stopwatch = True
            data['result'] = ''
        else:
            raise ValueError(data['individual_times'])
        tt = TimeTrial(profile=data['profile'],
                       result=data['result'],
                       start_time=data['start_time'],
                       creator=self.request.get_or_create_profile(),
                       created_time=now)
        tt.save()
        if stopwatch:
            return HttpResponseRedirect(
                reverse('timetrial_stopwatch',
                        kwargs={'pk': tt.pk}))
        for i, duration in enumerate(durations):
            leg = Leg(timetrial=tt,
                      duration=duration.total_seconds(),
                      order=i + 1)
            leg.save()
        logger.info("%s %s created by %s",
                    TimeTrial.objects.get(pk=tt.pk),
                    ' '.join(map(str, durations)),
                    self.request.profile,
                    extra=self.request.log_data)
        return HttpResponseRedirect(
            reverse('timetrial_detail',
                    kwargs={'pk': tt.pk}))


class TimeTrialStopwatchCreate(FormView):
    form_class = TimeTrialCreateForm
    template_name = 'stopwatch/timetrialstopwatchcreate.html'

    def get_initial(self):
        initial = {
            'profile': self.request.GET.get('profile', self.request.profile),
        }
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        now = timezone.now()
        tt = TimeTrial(profile=data['profile'],
                       result='',
                       start_time=data['start_time'],
                       creator=self.request.get_or_create_profile(),
                       created_time=now)
        tt.save()
        return HttpResponseRedirect(
            reverse('timetrial_stopwatch',
                    kwargs={'pk': tt.pk}))


def get_time_attack(current_timetrial, **kwargs):
    if 'prev' in kwargs:
        prev = kwargs.pop('prev')
        person = str(prev.profile)
    else:
        qs = TimeTrial.objects.filter(
            profile=current_timetrial.profile,
            result='f',
            leg_count=current_timetrial.leg_count or 5,
            created_time__lt=current_timetrial.created_time)
        qs = qs.order_by('duration')
        try:
            prev = qs[0]
        except IndexError:
            prev = None
        person = 'Personlig rekord'

    if kwargs:
        raise TypeError(', '.join(kwargs.keys()))

    if prev:
        durations = [int(1000 * l.duration) for l in prev.leg_set.all()]
        time_attack = {
            'person': person,
            'durations': durations,
        }
    else:
        time_attack = None

    return prev, time_attack


class TimeTrialStateMixin(object):
    def get_state(self):
        o = self.object
        prev, time_attack = get_time_attack(o)

        if o.start_time:
            now = timezone.now()
            start_time = o.start_time
            elapsed = (now - start_time).total_seconds()
        else:
            elapsed = 0
        durations = [l.duration for l in o.leg_set.all()]
        if o.result == 'dnf':
            state_display = 'DNF'
        elif o.result != '':
            state_display = o.get_result_display()
        else:
            state_display = 'Live'
        return {
            'elapsed_time': elapsed,
            'durations': durations,
            'state': o.state,
            'result': o.result,
            'result_display': o.get_result_display(),
            'time_attack': time_attack,
        }


class TimeTrialStopwatch(UpdateView, TimeTrialStateMixin):
    model = TimeTrial
    template_name = 'stopwatch/timetrialstopwatch.html'
    form_class = StopwatchForm
    queryset = TimeTrial.objects.all()

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.result != '':
            return HttpResponseRedirect(
                reverse('timetrial_detail', kwargs={'pk': object.pk}))
        else:
            return super(TimeTrialStopwatch, self).dispatch(
                request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['do_post'] = True
        kwargs['do_fetch'] = False
        state = self.get_state()
        kwargs['state'] = mark_safe(json.dumps(state))
        return super(TimeTrialStopwatch, self).get_context_data(**kwargs)

    def form_valid(self, form):
        if form.cleaned_data['beverage']:
            beverage, created = Beverage.objects.get_or_create(
                name=form.cleaned_data['beverage'])
        else:
            beverage = None
        self.object.beverage = beverage
        self.object.result = form.cleaned_data['result']
        self.object.start_time = form.cleaned_data['start_time']
        self.object.residue = form.cleaned_data['residue']
        self.object.comment = form.cleaned_data['comment']
        self.object.save_robust()
        self.object.set_legs(
            [d.total_seconds() for d in form.cleaned_data['durations']])
        for image in form.cleaned_data['images']:
            self.object.image_set.create(image=image)

        timetrial = TimeTrial.objects.get(pk=self.object.pk)
        durations = [l.duration for l in timetrial.leg_set.all()]
        logger.info("%s %s created with stopwatch by %s",
                    timetrial,
                    ' '.join(map(str, durations)),
                    self.request.profile,
                    extra=self.request.log_data)
        return HttpResponseRedirect(
            reverse('timetrial_detail', kwargs={'pk': self.object.pk}))


class TimeTrialLiveUpdate(BaseFormView):
    form_class = TimeTrialLiveForm

    def get(self, request, *args, **kwargs):
        tt = get_object_or_404(TimeTrial.objects, pk=self.kwargs['pk'])
        return HttpResponseRedirect(tt.get_absolute_url())

    def form_invalid(self, form):
        d = json.loads(form.errors.as_json())
        return JsonResponse(d, status_code=400)

    def form_valid(self, form):
        timetrial = form.cleaned_data['timetrial']
        if timetrial.creator != self.request.profile:
            return HttpResponseForbidden(
                'Access denied (only creator can update)')
        old_legs = [l.duration for l in timetrial.leg_set.all()]
        legs = [d.total_seconds() for d in form.cleaned_data['durations']]
        timetrial.result = ''
        timetrial.possible_laps = form.cleaned_data['possible_laps']
        timetrial.state = form.cleaned_data['state']

        elapsed_time = form.cleaned_data['elapsed_time']
        rt = form.cleaned_data['roundtrip_estimate']
        latency = datetime.timedelta(seconds=rt / 2)
        if not (old_legs and legs[:len(old_legs)] == old_legs):
            timetrial.start_time = timezone.now() - latency - elapsed_time

        timetrial.save_robust()

        if not legs and old_legs:
            logger.info("%s %s reset by %s",
                        timetrial,
                        ' '.join(map(str, old_legs)),
                        self.request.profile,
                        extra=self.request.log_data)
        timetrial.set_legs(legs)
        return HttpResponse('OK')


class TimeTrialStopwatchOffline(TemplateView):
    template_name = 'stopwatch/timetrialstopwatch.html'

    def get_context_data(self, **kwargs):
        kwargs['do_post'] = False
        kwargs['do_fetch'] = False
        kwargs['form'] = StopwatchForm(instance=TimeTrial(), initial={})
        return super(TimeTrialStopwatchOffline, self).get_context_data(
            **kwargs)


class TimeTrialStopwatchLive(DetailView, TimeTrialStateMixin):
    model = TimeTrial
    template_name = 'stopwatch/timetrialstopwatch.html'
    queryset = TimeTrial.objects.all()

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.result != '' and not self.request.is_ajax():
            return HttpResponseRedirect(
                reverse('timetrial_detail', kwargs={'pk': object.pk}))
        else:
            return super(TimeTrialStopwatchLive, self).dispatch(
                request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super(TimeTrialStopwatchLive, self).get_context_data(
            **kwargs)
        context_data['do_post'] = False
        context_data['do_fetch'] = True
        state = self.get_state()
        context_data['state'] = mark_safe(json.dumps(state))
        return context_data

    def render_to_response(self, context, **kwargs):
        if self.request.is_ajax():
            return JsonResponse(self.get_state())
        else:
            return super(TimeTrialStopwatchLive, self).render_to_response(
                context, **kwargs)


class TimeTrialDetail(DetailView):
    model = TimeTrial
    template_name = 'stopwatch/timetrialdetail.html'

    def get_context_data(self, **kwargs):
        context_data = super(TimeTrialDetail, self).get_context_data(**kwargs)
        if 'previous' in self.request.GET:
            prev_pk = self.request.GET['previous']
            try:
                prev = TimeTrial.objects.get(pk=int(prev_pk))
            except:
                prev = None
            prev, time_attack = get_time_attack(
                context_data['object'], prev=prev)
        else:
            prev, time_attack = get_time_attack(context_data['object'])
        laps = list(context_data['object'].leg_set.all())
        for leg in laps:
            leg.diff = None
        if prev:
            for leg, prev_leg in zip(laps, prev.leg_set.all()):
                leg.diff = leg.duration_prefix_sum - prev_leg.duration_prefix_sum
            context_data['prev'] = prev
            context_data['prev_person'] = time_attack['person']
        context_data['laps'] = laps
        return context_data


class TimeTrialTimeline(DetailView):
    model = TimeTrial
    template_name = 'stopwatch/timetrialtimeline.html'

    def get_context_data(self, **kwargs):
        context_data = (
            super(TimeTrialTimeline, self).get_context_data(**kwargs))
        o = context_data['object']
        window = datetime.timedelta(seconds=30)
        timetrials = TimeTrial.objects.filter(
            start_time__gt=o.start_time - window,
            start_time__lt=o.start_time + window)
        timetrials = timetrials.order_by('duration')
        context_data['object_list'] = timetrials
        context_data['duration'] = max(tt.duration for tt in timetrials)
        return context_data


class TimeTrialList(ListView):
    template_name = 'stopwatch/timetriallist.html'

    def get_queryset(self):
        queryset = (
            TimeTrial.objects.exclude(result='')
            .order_by('-start_time')
        )
        return self.request.filter_association(queryset)


class TimeTrialUpdate(UpdateView):
    form_class = TimeTrialForm
    template_name = 'stopwatch/timetrialupdate.html'
    queryset = TimeTrial.objects.all()

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return permission_denied(request, exception=None)
        return super(TimeTrialUpdate, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        timetrial = context_data['object']
        try:
            context_data['possible_laps'] = timetrial.parse_possible_laps()
        except ValidationError:
            pass
        return context_data


class TimeTrialAllBest(TemplateView):
    template_name = 'stopwatch/timetrialallbest.html'

    def get_context_data(self, **kwargs):
        context_data = super(TimeTrialAllBest, self).get_context_data(**kwargs)
        if self.kwargs['season'] == 'current':
            season_start = Home.get_season_start()
            context_data['timetrial_list'] = self.get_timetrial_list(
                start_time__gt=season_start)
        else:
            context_data['timetrial_list'] = self.get_timetrial_list()
        return context_data

    def get_timetrial_list(self, **kwargs):
        qs = TimeTrial.objects.filter(result='f', **kwargs)
        qs = self.request.filter_association(qs)
        qs = qs.order_by('leg_count', 'duration')
        try:
            qs_distinct = qs.distinct('leg_count')
            return list(qs_distinct)
        except (NotImplementedError, FieldError):
            res = {}
            for tt in qs:
                res.setdefault(tt.leg_count, tt)
            return sorted(res.values(), key=lambda tt: tt.leg_count)


class TimeTrialBest(TemplateView):
    template_name = 'stopwatch/timetriallist.html'

    def get_context_data(self, **kwargs):
        context_data = super(TimeTrialBest, self).get_context_data(**kwargs)
        if self.kwargs['season'] == 'current':
            season_start = Home.get_season_start()
            context_data['timetrial_list'] = self.get_timetrial_list(
                start_time__gt=season_start)
        else:
            context_data['timetrial_list'] = self.get_timetrial_list()
        context_data['list_legs'] = self.kwargs['legs']
        return context_data

    def get_timetrial_list(self, **kwargs):
        qs = (
            TimeTrial.leg_prefix(int(self.kwargs['legs']))
            .filter(result='f', **kwargs)
            .order_by('duration')
        )
        qs = self.request.filter_association(qs)
        try:
            qs_distinct = qs.distinct('profile')
            return list(qs_distinct)
        except NotImplementedError:
            res = {}
            for tt in qs:
                res.setdefault(tt.profile_id, tt)
            return sorted(res.values(), key=lambda tt: tt.duration)


class IndentJSONEncoder(DjangoJSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs['indent'] = 2
        return super(IndentJSONEncoder, self).__init__(*args, **kwargs)


class Json(View):
    def get(self, request, *args, **kwargs):
        data = []
        qs = TimeTrial.raw_objects.all()
        leg_qs = Leg.raw_objects.all()
        profile_qs = Profile.objects.all()
        if self.kwargs.get('live'):
            now = timezone.now()
            threshold = now - datetime.timedelta(hours=1)
            qs = qs.filter(result='', start_time__gt=threshold)
            leg_qs = leg_qs.filter(timetrial__in=qs)

        profile_qs = profile_qs.order_by()
        profile_qs = profile_qs.values_list(
            'id', 'title__period', 'title__title', 'name', 'association_id', 'association__current_period', 'association__name')
        names = {}
        associations = {}
        for profile_id, title_period, title, name, a_id, a_period, a_name in profile_qs:
            dummy = Profile()
            dummy.pk = profile_id
            dummy_a = Association()
            dummy_a.pk = a_id
            dummy_a.name = a_name
            dummy_a.current_period = a_period
            dummy_t = Title(association=dummy_a, period=title_period, title=title)
            dummy.title = dummy_t if title else None
            dummy.name = name
            names[profile_id] = str(dummy)
            associations[profile_id] = a_id

        leg_qs = leg_qs.order_by()
        leg_qs = leg_qs.values_list('timetrial_id', 'duration', 'order')
        legs = {}
        for tt_id, duration, order in leg_qs:
            legs.setdefault(tt_id, []).append((order, duration))

        qs = qs.values_list(
            'id', 'start_time', 'profile_id',
            'result', 'comment', 'residue',
        )

        for tt_id, start_time, profile_id, result, comment, residue in qs:
            durations = [d for o, d in sorted(legs.get(tt_id, ()))]
            tt_data = {
                'id': tt_id,
                'start_time': str(start_time),
                'profile_id': profile_id,
                'profile': names.get(profile_id),
                'association': associations.get(profile_id),
                'result': result,
                'comment': comment,
                'residue': residue,
                'durations': durations,
            }
            data.append(tt_data)
        response = JsonResponse(data, safe=False, encoder=IndentJSONEncoder)
        response['Access-Control-Allow-Origin'] = '*'
        return response


class ImageList(ListView):
    model = Image
    template_name = 'stopwatch/image_list.html'
    # paginate_by = 30
    ordering = ['-created_time']
