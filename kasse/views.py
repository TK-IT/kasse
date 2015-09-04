# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import json
import datetime

from django.core.exceptions import FieldError
from django.core.urlresolvers import reverse
from django.db import OperationalError
from django.utils.safestring import mark_safe
from django.http import (
    HttpResponse, JsonResponse, HttpResponseRedirect,
    HttpResponseForbidden,
)
from django.views.generic import (
    View, TemplateView, FormView, DetailView, ListView, UpdateView,
)
from django.views.generic.edit import BaseFormView
from django.views.defaults import permission_denied
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.forms.utils import to_current_timezone

from kasse.forms import (
    TimeTrialCreateForm, LoginForm, ProfileCreateForm,
    ProfileEditForm,
    StopwatchForm, TimeTrialLiveForm,
)
from kasse.models import TimeTrial, Leg, Title, Profile


class Home(TemplateView):
    template_name = 'kasse/home.html'

    @staticmethod
    def get_latest():
        qs = TimeTrial.objects.all()
        qs = qs.exclude(result='')
        qs = qs.order_by('-start_time')
        return list(qs[:5])

    @staticmethod
    def get_best(**kwargs):
        limit = kwargs.pop('limit', None)
        leg_count = kwargs.pop('leg_count', 5)
        qs = TimeTrial.objects.all()
        if kwargs:
            qs = qs.filter(**kwargs)
        qs = qs.exclude(result='')
        qs = qs.filter(leg_count=leg_count)
        qs = qs.order_by('duration')
        try:
            qs_distinct = qs.distinct('profile')
            return list(qs_distinct[:limit])
        except NotImplementedError:
            res = {}
            for tt in qs:
                res.setdefault(tt.profile_id, tt)
                if limit is not None and len(res) >= limit:
                    break
            return sorted(res.values(), key=lambda tt: tt.duration)

    @staticmethod
    def get_season_start():
        return datetime.date(2015, 8, 1)

    @staticmethod
    def get_current_best(**kwargs):
        season_start = Home.get_season_start()
        return Home.get_best(start_time__gt=season_start, **kwargs)

    @staticmethod
    def get_live():
        qs = TimeTrial.objects.all()
        qs = qs.filter(result='')
        now = datetime.datetime.now()
        threshold = now - datetime.timedelta(hours=1)
        qs = qs.filter(start_time__gt=threshold)
        return list(qs)

    def get_context_data(self, **kwargs):
        context_data = super(Home, self).get_context_data(**kwargs)
        context_data['live'] = self.get_live()
        context_data['latest'] = self.get_latest()
        context_data['best'] = self.get_best(limit=5)
        season_start = self.get_season_start()
        context_data['current_season'] = '%d/%d' % (
            season_start.year, season_start.year - 2000 + 1)
        context_data['current_season_best'] = self.get_current_best(limit=5)
        return context_data


class Login(FormView):
    form_class = LoginForm
    template_name = 'kasse/login.html'

    def get_initial(self):
        return {'next': reverse('home')}

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = User.objects.get(username=username)

        if user is None:
            form.add_error('username', 'Ugyldigt brugernavn')
            return self.form_invalid(form)

        user = authenticate(username=username, password=password)
        if user is None:
            form.add_error('password', 'Forkert kodeord')
            return self.form_invalid(form)

        login(self.request, user)

        return HttpResponseRedirect(form.cleaned_data['next'])


class Logout(View):
    def post(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('home'))


class ChangePassword(FormView):
    form_class = PasswordChangeForm
    template_name = 'kasse/changepassword.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('home'))
        else:
            return super(ChangePassword, self).dispatch(
                request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ChangePassword, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('home'))


class TimeTrialCreate(FormView):
    form_class = TimeTrialCreateForm
    template_name = 'kasse/timetrialcreateform.html'

    def get_initial(self):
        initial = {'profile': self.request.profile}
        for k, v in self.request.GET.items():
            initial[k] = v
        try:
            initial['start_time'] = datetime.datetime.fromtimestamp(
                float(initial['start_time']))
        except KeyError:
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
        now = datetime.datetime.now()
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
        return HttpResponseRedirect(
            reverse('timetrial_detail',
                    kwargs={'pk': tt.pk}))


class TimeTrialStopwatchCreate(FormView):
    form_class = TimeTrialCreateForm
    template_name = 'kasse/timetrialstopwatchcreate.html'

    def get_initial(self):
        initial = {'profile': self.request.profile}
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        now = datetime.datetime.now()
        tt = TimeTrial(profile=data['profile'],
                       result='',
                       start_time=data['start_time'],
                       creator=self.request.get_or_create_profile(),
                       created_time=now)
        tt.save()
        return HttpResponseRedirect(
            reverse('timetrial_stopwatch',
                    kwargs={'pk': tt.pk}))


class TimeTrialStateMixin(object):
    def get_state(self):
        o = self.object
        if o.start_time:
            now = datetime.datetime.now()
            start_time = to_current_timezone(o.start_time)
            elapsed = (now - start_time).total_seconds()
        else:
            elapsed = 0
        durations = [l.duration for l in o.leg_set.all()]
        return {
            'elapsed_time': elapsed,
            'durations': durations,
            'state': o.result or o.state,
        }


class TimeTrialStopwatch(UpdateView, TimeTrialStateMixin):
    model = TimeTrial
    template_name = 'kasse/timetrialstopwatch.html'
    form_class = StopwatchForm
    queryset = TimeTrial.objects.filter(result='')

    def get_context_data(self, **kwargs):
        kwargs['do_post'] = True
        kwargs['do_fetch'] = False
        state = self.get_state()
        kwargs['state'] = mark_safe(json.dumps(state))
        return super(TimeTrialStopwatch, self).get_context_data(**kwargs)

    def form_valid(self, form):
        self.object.result = form.cleaned_data['result']
        self.object.start_time = form.cleaned_data['start_time']
        try:
            self.object.save()
        except OperationalError:
            # Work around bug in SQLite
            # Related to: https://code.djangoproject.com/ticket/18580
            TimeTrial.objects.filter(pk=self.object.pk).values('id').update(
                result=form.cleaned_data['result'],
                start_time=form.cleaned_data['start_time'],
            )
        self.object.leg_set.all().delete()
        self.object.leg_set = [
            Leg(duration=d.total_seconds(), order=i + 1)
            for i, d in enumerate(form.cleaned_data['durations'])
        ]
        # self.object.durations.save()
        return HttpResponseRedirect(
            reverse('timetrial_detail', kwargs={'pk': self.object.pk}))


class TimeTrialLiveUpdate(BaseFormView):
    form_class = TimeTrialLiveForm

    def form_valid(self, form):
        timetrial = form.cleaned_data['timetrial']
        if timetrial.creator != self.request.profile:
            return HttpResponseForbidden(
                'Access denied (only creator can update)')
        timetrial.result = ''
        timetrial.state = form.cleaned_data['state']

        elapsed_time = form.cleaned_data['elapsed_time']
        rt = form.cleaned_data['roundtrip_estimate']
        latency = datetime.timedelta(seconds=rt / 2)
        timetrial.start_time = datetime.datetime.now() - latency - elapsed_time

        timetrial.save()

        timetrial.leg_set.all().delete()
        timetrial.leg_set = [
            Leg(duration=d.total_seconds(), order=i + 1)
            for i, d in enumerate(form.cleaned_data['durations'])
        ]
        return HttpResponse('OK')


class TimeTrialStopwatchOffline(TemplateView):
    template_name = 'kasse/timetrialstopwatch.html'

    def get_context_data(self, **kwargs):
        kwargs['do_post'] = False
        kwargs['do_fetch'] = False
        return super(TimeTrialStopwatchOffline, self).get_context_data(
            **kwargs)


class TimeTrialStopwatchLive(DetailView, TimeTrialStateMixin):
    model = TimeTrial
    template_name = 'kasse/timetrialstopwatch.html'
    queryset = TimeTrial.objects.all()

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
    template_name = 'kasse/timetrialdetail.html'


class TimeTrialList(ListView):
    queryset = (
        TimeTrial.objects.exclude(result='')
        .order_by('-start_time')
    )
    template_name = 'kasse/timetriallist.html'


class TimeTrialAllBest(TemplateView):
    template_name = 'kasse/timetrialallbest.html'

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
    template_name = 'kasse/timetriallist.html'

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
            TimeTrial.objects.filter(result='f')
            .filter(leg_count=int(self.kwargs['legs']), **kwargs)
            .order_by('duration')
        )
        try:
            qs_distinct = qs.distinct('profile')
            return list(qs_distinct)
        except NotImplementedError:
            res = {}
            for tt in qs:
                res.setdefault(tt.profile_id, tt)
            return sorted(res.values(), key=lambda tt: tt.duration)


class ProfileCreate(FormView):
    form_class = ProfileCreateForm
    template_name = 'kasse/profilecreateform.html'

    def form_valid(self, form):
        name = form.cleaned_data['name']
        title = form.cleaned_data['title']
        period = form.cleaned_data['period']
        association = form.cleaned_data['association']
        if title:
            t = Title(
                association=association, period=period, title=title)
            t.save()
        else:
            t = None
        p = Profile(name=name, title=t, association=association)
        p.save()
        return HttpResponseRedirect(reverse('home'))


class ProfileView(DetailView):
    template_name = 'kasse/profile.html'
    model = Profile

    def get_context_data(self, **kwargs):
        context_data = super(ProfileView, self).get_context_data(**kwargs)
        context_data['is_self'] = self.request.profile == self.object
        return context_data


class ProfileEditBase(UpdateView):
    template_name = 'kasse/profile_edit.html'
    model = Profile
    form_class = ProfileEditForm

    def get_success_url(self):
        return reverse('profile', kwargs={'pk': self.object.pk})


class ProfileEdit(ProfileEditBase):
    def get_object(self):
        return self.request.profile


class ProfileEditAdmin(ProfileEditBase):
    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            return permission_denied(request)
        return super(ProfileEditAdmin, self).dispatch(request, *args, **kwargs)
