# vim: set fileencoding=utf8:
from __future__ import absolute_import, unicode_literals, division

from django.db import models
from django.db.models import Sum, Count, ExpressionWrapper

from kasse.models import Profile

from iou.managers import ExpenceManager, ProfileManager


class ExpenceProfile(Profile):
    objects = ProfileManager()

    @property
    def balance(self):
        try:
            return self._balance
        except AttributeError as e:
            self._balance = self.compute_balance()
            return self._balance

    @balance.setter
    def balance(self, v):
        self._balance = v

    def compute_balance(self):
        amount_field = Expence._meta.get_field('amount')
        exp1 = Sum('amount')
        exp2 = ExpressionWrapper(exp1 / Count('consumers'),
                                 output_field=amount_field)
        a = self.expence_paid_set.all().aggregate(a=exp1)['a'] or 0
        b = Expence.objects.filter(consumers=self).aggregate(a=Sum('amount_each', output_field=amount_field))['a'] or 0
        return a - b

    class Meta:
        proxy = True


class Expence(models.Model):
    objects = ExpenceManager()

    payer = models.ForeignKey(Profile, related_name='expence_paid_set')
    consumers = models.ManyToManyField(
        Profile, related_name='expence_consumed_set')
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    comment = models.TextField(blank=True)


def move_profile(target, destination):
    Expence.objects.filter(payer=target).update(payer=destination)
    consumers = Expence.consumers.through
    consumers.objects.filter(profile=target).update(profile=destination)
