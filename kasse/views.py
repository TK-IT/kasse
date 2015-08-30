# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import datetime

from django.core.exceptions import ValidationError, FieldError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import (
    View, TemplateView, FormView, DetailView, ListView,
)
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from kasse.forms import TimeTrialCreateForm, LoginForm, ProfileCreateForm
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
        qs = TimeTrial.objects.all()
        if kwargs:
            qs = qs.filter(**kwargs)
        qs = qs.exclude(result='')
        qs = qs.filter(leg_count=5)
        qs = qs.order_by('duration')
        try:
            qs_distinct = qs.distinct('profile')
            return list(qs_distinct[:5])
        except NotImplementedError:
            res = {}
            for tt in qs:
                res.setdefault(tt.profile_id, tt)
                if len(res) >= 5:
                    break
            return sorted(res.values(), key=lambda tt: tt.duration)

    def get_context_data(self, **kwargs):
        context_data = super(Home, self).get_context_data(**kwargs)
        context_data['latest'] = self.get_latest()
        context_data['best'] = self.get_best()
        season_start = datetime.date(2015, 8, 1)
        context_data['current_season'] = '%d/%d' % (
            season_start.year, season_start.year - 2000 + 1)
        current_season_best = self.get_best(start_time__gt=season_start)
        context_data['current_season_best'] = current_season_best
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


class TimeTrialCreate(FormView):
    form_class = TimeTrialCreateForm
    template_name = 'kasse/timetrialcreateform.html'

    def get_initial(self):
        return {'profile': self.request.profile}

    def form_valid(self, form):
        data = form.cleaned_data
        now = datetime.datetime.now()
        if data['individual_times'] == 'individual':
            durations = data['durations']
        elif data['individual_times'] == 'total':
            zero = datetime.timedelta(seconds=0)
            durations = [zero] * (data['legs'] - 1) + [data['total_time']]
        duration_sum = sum(
            duration.total_seconds()
            for duration in durations
        )

        tt = TimeTrial(profile=data['profile'],
                       result=data['result'],
                       start_time=data['start_time'],
                       creator=self.request.get_or_create_profile(),
                       created_time=now,
                       duration=duration_sum)
        tt.save()
        for i, duration in enumerate(durations):
            leg = Leg(timetrial=tt,
                      duration=duration.total_seconds(),
                      order=i + 1)
            leg.save()
        return HttpResponseRedirect(
            reverse('timetrial_detail',
                    kwargs={'pk': tt.pk}))


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
        context_data['timetrial_list'] = self.get_timetrial_list()
        return context_data

    def get_timetrial_list(self):
        qs = TimeTrial.objects.filter(result='f')
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
        context_data['timetrial_list'] = self.get_timetrial_list()
        context_data['list_legs'] = self.kwargs['legs']
        return context_data

    def get_timetrial_list(self):
        qs = (
            TimeTrial.objects.filter(result='f')
            .filter(leg_count=int(self.kwargs['legs']))
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
