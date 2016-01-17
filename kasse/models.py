# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.contrib.auth.models import User

from kasse.managers import ProfileManager
from kasse.fields import APeriodField


@python_2_unicode_compatible
class Association(models.Model):
    name = models.CharField(max_length=200)
    current_period = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    @classmethod
    def none_string(cls):
        return '(independent)'


@python_2_unicode_compatible
class Title(models.Model):
    association = models.ForeignKey(Association)
    period = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=200)

    @staticmethod
    def sup(n):
        digits = '⁰¹²³⁴⁵⁶⁷⁸⁹'
        return ''.join(digits[int(i)] for i in str(n))

    @staticmethod
    def tk_prefix(age):
        prefix = ['', 'G', 'B', 'O', 'TO']
        if age < 0:
            return 'K%s' % Title.sup(-age)
        elif age < len(prefix):
            return prefix[age]
        else:
            return 'T%sO' % Title.sup(age - 3)

    def tk_str(self):
        enable_efuit = False
        if enable_efuit and self.title == 'EFUIT':
            years = [2015, 2014, 2013, 2011, 2010]
            age = 0
            while age < len(years) and self.period < years[age]:
                age += 1
        else:
            age = self.association.current_period - self.period
        return '%s%s' % (self.tk_prefix(age), self.title)

    def a_str(self):
        return '%s %s' % (
            self.title, APeriodField.static_prepare_value(self.period))

    def def_str(self):
        return '%s %s' % (self.title, self.period)

    def __str__(self):
        p = self.period
        if p is None:
            s = self.title
        elif self.association.name == 'TÅGEKAMMERET':
            s = self.tk_str()
        elif self.association.name == '@lkymia':
            s = self.a_str()
        else:
            s = self.def_str()
        return s or '(blank)'

    class Meta:
        ordering = ['association', 'period', 'title']


@python_2_unicode_compatible
class Profile(models.Model):
    objects = ProfileManager()

    user = models.OneToOneField(User, null=True, blank=True,
                                on_delete=models.SET_NULL)
    name = models.CharField(max_length=200, blank=True, verbose_name='Navn')
    title = models.OneToOneField(Title, null=True, blank=True,
                                 on_delete=models.SET_NULL)
    association = models.ForeignKey(Association, null=True, blank=True,
                                    on_delete=models.SET_NULL)

    favorite_drink = models.CharField(max_length=200, blank=True,
                                      verbose_name='Yndlingsøl')

    created_time = models.DateTimeField(auto_now_add=True)

    @classmethod
    def all_named(cls):
        return cls.objects.exclude(name='', title__isnull=True)

    def get_anonymous(self):
        return not self.name and not self.title
    get_anonymous.boolean = True
    get_anonymous.short_description = 'Anonym'
    is_anonymous = property(get_anonymous)

    def clean(self):
        if self.user and not (self.name or self.title):
            raise ValidationError(
                'Name or title is required for non-anonymous profile')

    def get_association_display(self):
        if self.association:
            return self.association
        else:
            return Association.none_string()

    def set_title(self, title, period):
        association = self.association
        new_title = (title, period, association)
        if self.title:
            if self.title.title == '':
                # Title can't be blank -- choose a current_title
                # that is definitely not equal to new_title
                current_title = ()
            else:
                current_title = (
                    self.title.title,
                    self.title.period,
                    self.title.association,
                )
        else:
            current_title = '', None, None
        if new_title != current_title:
            if self.title:
                self.title.delete()
            if title:
                t = Title(title=title, period=period, association=association)
                t.save()
                self.title = t
            else:
                self.title = None

    def __str__(self):
        if self.title and self.name:
            return '%s %s' % (self.title, self.name)
        elif self.title:
            return '%s' % (self.title,)
        elif self.name:
            return '%s' % (self.name,)
        else:
            return '(anonymous %s)' % (self.pk,)
