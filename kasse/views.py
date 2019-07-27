# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

import logging
import datetime
import functools

from django.urls import reverse
from django.utils.six.moves import urllib_parse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.http import (
    HttpResponse, HttpResponseRedirect,
    Http404,
)
from django.views.generic import (
    View, TemplateView, FormView, DetailView, UpdateView, ListView, CreateView,
)
from django.views.defaults import permission_denied
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.conf import settings
from django.db.utils import NotSupportedError
from django.db.models import Count
from django.shortcuts import get_object_or_404

from kasse.forms import (
    LoginForm, ProfileCreateForm,
    ProfileEditForm, UserCreationForm,
    AssociationForm, ProfileMergeForm,
    ContestForm, AssociationPeriodForm,
)
from kasse.models import Profile, Contest
import kasse.models

import stopwatch.models
import iou.models
from stopwatch.models import TimeTrial

logger = logging.getLogger('kasse')


def dispatch_superuser_required(function):
    @functools.wraps(function)
    def dispatch(request, *args, **kwargs):
        if not request.user.is_superuser:
            return permission_denied(request, exception=None)
        return function(request, *args, **kwargs)

    return dispatch


superuser_required = method_decorator(
    dispatch_superuser_required, name='dispatch')


class Home(TemplateView):
    template_name = 'kasse/home.html'

    def get_latest(self):
        qs = TimeTrial.objects.all()
        qs = self.request.filter_association(qs)
        qs = qs.exclude(result='')
        qs = qs.order_by('-start_time')
        return list(qs[:5])

    def get_best(self, **kwargs):
        limit = kwargs.pop('limit', None)
        leg_count = kwargs.pop('leg_count', 5)
        qs = TimeTrial.objects.all()
        qs = self.request.filter_association(qs)
        if kwargs:
            qs = qs.filter(**kwargs)
        qs = qs.filter(result='f', leg_count=leg_count)
        qs = qs.order_by('duration')
        try:
            qs_distinct = qs.distinct('profile')
            return list(qs_distinct[:limit])
        except (NotImplementedError, NotSupportedError):
            res = {}
            for tt in qs:
                res.setdefault(tt.profile_id, tt)
                if limit is not None and len(res) >= limit:
                    break
            return sorted(res.values(), key=lambda tt: tt.duration)

    @staticmethod
    def get_season_start():
        return datetime.date(2018, 10, 5)

    def get_current_best(self, **kwargs):
        season_start = Home.get_season_start()
        return self.get_best(start_time__gt=season_start, **kwargs)

    def get_live(self):
        qs = TimeTrial.objects.all()
        # qs = self.request.filter_association(qs)
        qs = qs.filter(result='')
        now = timezone.now()
        threshold = now - datetime.timedelta(hours=1)
        qs = qs.filter(start_time__gt=threshold)
        return list(qs)

    def get_context_data(self, **kwargs):
        context_data = super(Home, self).get_context_data(**kwargs)
        context_data['login_form'] = LoginForm()
        context_data['live'] = self.get_live()
        context_data['latest'] = self.get_latest()
        context_data['best'] = self.get_best(limit=5)
        season_start = self.get_season_start()
        context_data['current_season'] = '%d/%d' % (
            season_start.year, season_start.year - 2000 + 1)
        context_data['current_season_best'] = self.get_current_best(limit=5)
        context_data['association_form'] = AssociationForm(
            initial={'association': self.request.association}
        )
        context_data['contests'] = Contest.objects.all().reverse()
        return context_data


class Login(FormView):
    form_class = LoginForm
    template_name = 'kasse/login.html'

    def get_initial(self):
        return {'next': reverse('home')}

    def form_valid(self, form):
        profile = form.cleaned_data['profile']
        user = profile.user
        if user is None:
            url = '%s?next=%s' % (
                reverse('newuser', kwargs={'pk': profile.pk}),
                urllib_parse.quote(form.cleaned_data['next']))
            return HttpResponseRedirect(url)

        password = form.cleaned_data['password']

        user = authenticate(username=user.username, password=password)
        if user is None:
            form.add_error('password', 'Forkert kodeord')
            return self.form_invalid(form)

        login(self.request, user)
        logger.info("Login %s", profile,
                    extra=self.request.log_data)

        return HttpResponseRedirect(form.cleaned_data['next'])


class Logout(View):
    def post(self, request):
        if request.profile:
            logger.info("Logout %s", request.profile,
                        extra=self.request.log_data)
        logout(request)
        return HttpResponseRedirect(reverse('home'))


class ChangePassword(FormView):
    form_class = PasswordChangeForm
    template_name = 'kasse/changepassword.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
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
        logger.info("Change password for %s", self.request.profile,
                    extra=self.request.log_data)
        return HttpResponseRedirect(reverse('home'))


class ProfileCreate(FormView):
    form_class = ProfileCreateForm
    template_name = 'kasse/profilecreateform.html'

    def form_valid(self, form):
        p = Profile()
        form.save(p)
        p.save()
        logger.info("Profile %s created by %s",
                    p, self.request.get_or_create_profile(),
                    extra=self.request.log_data)

        r = self.request.GET.get('r')
        if r == 'ttc':
            d = 'timetrial_create'
            qs = '?profile=%d' % p.pk
        elif r == 'sw':
            d = 'timetrial_stopwatch_create'
            qs = '?profile=%d' % p.pk
        else:
            d = 'home'
            qs = ''
        success_url = reverse(d) + qs
        return HttpResponseRedirect(success_url)


class ProfileView(DetailView):
    template_name = 'kasse/profile.html'
    model = Profile

    def get_context_data(self, **kwargs):
        context_data = super(ProfileView, self).get_context_data(**kwargs)
        context_data['is_self'] = self.request.profile == self.object
        qs = self.object.timetrial_profile_set.all()
        qs = qs.exclude(result='')
        qs = qs.order_by('-start_time')
        context_data['timetrial_list'] = qs
        context_data['leg_count'] = sum(len(tt.leg_set.all()) for tt in qs)
        return context_data


class ProfileList(ListView):
    template_name = 'kasse/profile_list.html'
    model = Profile

    def get_queryset(self):
        qs = Profile.all_named()
        qs = qs.annotate(timetrial_count=Count('timetrial_profile_set'))
        qs = qs.order_by('-timetrial_count')
        return qs


@superuser_required
class ProfileMerge(FormView):
    template_name = 'kasse/profile_merge.html'
    form_class = ProfileMergeForm

    def get_context_data(self, **kwargs):
        context_data = super(ProfileMerge, self).get_context_data(**kwargs)
        context_data['target'] = self.get_target()
        return context_data

    def get_target(self):
        return get_object_or_404(
            Profile.all_named(), pk=self.kwargs['pk'])

    def form_valid(self, form):
        target = self.get_target()
        destination = form.cleaned_data['destination']
        if target == destination:
            form.add_error('destination', 'Kan ikke overflytte til sig selv')
            return self.form_invalid(form)
        stopwatch.models.move_profile(target, destination)
        iou.models.move_profile(target, destination)
        logger.info("Profile %s merged into %s by %s",
                    target, destination,
                    self.request.profile,
                    extra=self.request.log_data)
        target.association = None
        target.set_title('', None)
        target.name = ''
        target.save()
        success_url = reverse('profile', kwargs={'pk': destination.pk})
        return HttpResponseRedirect(success_url)


class ProfileEditBase(UpdateView):
    template_name = 'kasse/profile_edit.html'
    model = Profile
    form_class = ProfileEditForm

    def get_success_url(self):
        return reverse('profile', kwargs={'pk': self.object.pk})


class ProfileEdit(ProfileEditBase):
    def get_object(self):
        p = self.request.profile
        if p == None:  # noqa (SimpleLazyObject)
            raise Http404()
        if p.is_anonymous:
            raise Http404()
        return p

    def form_valid(self, form):
        response = super(ProfileEdit, self).form_valid(form)
        logger.info("%s edited own profile",
                    self.request.profile,
                    extra=self.request.log_data)
        return response


@superuser_required
class ProfileEditAdmin(ProfileEditBase):
    def form_valid(self, form):
        response = super(ProfileEditAdmin, self).form_valid(form)
        logger.info("Admin %s edited profile of %s",
                    self.request.profile,
                    self.object,
                    extra=self.request.log_data)
        return response


class UserCreate(TemplateView):
    template_name = 'kasse/usercreateform.html'

    def get_profile(self):
        return get_object_or_404(
            Profile, pk=self.kwargs['pk'],
            user__isnull=True)

    def get_initial(self):
        if 'pk' in self.kwargs:
            profile = self.get_profile()
            initial = {
                'username': 'profile%d' % profile.pk,
                'name': profile.name,
                'association': profile.association,
            }
            if profile.title:
                initial.update({
                    'title': profile.title.title,
                    'period': profile.title.period,
                })
        else:
            initial = {
                'username': 'placeholder',
            }
        return initial

    def get_forms(self):
        kwargs = {
            'initial': self.get_initial(),
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST.copy()
            kwargs['data']['username'] = kwargs['initial']['username']
        user_form = UserCreationForm(**kwargs)
        profile_form = ProfileCreateForm(**kwargs)
        return user_form, profile_form

    def get(self, request, *args, **kwargs):
        user_form, profile_form = self.get_forms()
        context_data = self.get_context_data(
            user_form=user_form, profile_form=profile_form)
        return self.render_to_response(context_data)

    def post(self, request, *args, **kwargs):
        user_form, profile_form = self.get_forms()
        if user_form.is_valid() and profile_form.is_valid():
            return self.form_valid(user_form, profile_form)
        else:
            return self.form_invalid(user_form, profile_form)

    def form_valid(self, user_form, profile_form):
        if 'pk' in self.kwargs:
            profile = self.get_profile()
        else:
            profile = Profile()
        profile_form.save(profile)
        profile.save()
        user = user_form.save()
        user.username = 'profile%d' % profile.pk
        user.save()
        profile.user = user
        profile.save()
        logger.info("Create user %s from profile %s",
                    user.username, profile,
                    extra=self.request.log_data)
        return HttpResponseRedirect(
            reverse('home'))

    def form_invalid(self, user_form, profile_form):
        context_data = self.get_context_data(
            user_form=user_form, profile_form=profile_form)
        return self.render_to_response(context_data)


@superuser_required
class Log(View):
    def get(self, request):
        filename = settings.LOGGING['handlers']['file']['filename']
        with open(filename, encoding='utf8') as fp:
            s = fp.read()
        return HttpResponse(s, content_type='text/plain; charset=utf8')


class Association(FormView):
    form_class = AssociationForm
    template_name = 'kasse/association.html'

    def form_valid(self, form):
        association = form.cleaned_data['association']
        self.request.set_association(association)
        ret = self.request.GET.get('return')
        if ret == 'home':
            return HttpResponseRedirect(reverse('home'))
        return self.get(self.request)

    def get_initial(self):
        return {'association': self.request.association}

    def get_context_data(self, **kwargs):
        context_data = super(Association, self).get_context_data(**kwargs)
        context_data['association'] = self.request.association
        return context_data


@superuser_required
class ContestCreate(CreateView):
    form_class = ContestForm
    template_name = 'kasse/contestform.html'

    def get_success_url(self):
        return reverse('home')


@superuser_required
class AssociationPeriodUpdate(FormView):
    form_class = AssociationPeriodForm
    template_name = 'kasse/associationperiodform.html'

    def get_association(self):
        return kasse.models.Association.objects.get(pk=1)

    def get_period(self):
        d = datetime.date.today()
        return d.year

    def get_titles(self):
        titles = 'CERM FORM INKA KA$$ NF PR SEKR VC'.split()
        return [(title.replace('$', 'S'), title) for title in titles]

    def get_form_kwargs(self, **kwargs):
        data = super(AssociationPeriodUpdate, self).get_form_kwargs(**kwargs)
        data['titles'] = self.get_titles()
        qs = Profile.all_named().filter(association=self.get_association())
        qs = qs.order_by('display_name')
        data['profiles'] = qs
        return data

    def get_context_data(self, **kwargs):
        data = super(AssociationPeriodUpdate, self).get_context_data(**kwargs)
        data['period'] = self.get_period()
        data['association'] = self.get_association()
        return data

    def form_valid(self, form):
        association = self.get_association()
        association.current_period = self.get_period()
        association.save()
        for key, title in self.get_titles():
            if form.cleaned_data[key]:
                form.cleaned_data[key].set_title(title, self.get_period())
                form.cleaned_data[key].save()
        context_data = self.get_context_data(form=form, message='Gemt!')
        return self.render_to_response(context_data)
