from __future__ import absolute_import, unicode_literals, division

import datetime

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import (
    View, TemplateView, FormView, DetailView, ListView,
)
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Count

from kasse.forms import TimeTrialCreateForm, LoginForm
from kasse.models import TimeTrial, Leg


class Home(TemplateView):
    template_name = 'kasse/home.html'


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
        duration_sum = sum(
            duration.total_seconds()
            for duration in data['durations']
        )

        tt = TimeTrial(profile=data['profile'],
                       result=data['result'],
                       start_time=data['start_time'],
                       creator=self.request.get_or_create_profile(),
                       created_time=now,
                       duration=duration_sum)
        tt.save()
        for i, duration in enumerate(data['durations']):
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
        .annotate(leg_count=Count('leg'))
        .order_by('-start_time')
    )
    template_name = 'kasse/timetriallist.html'
