import sys


from django.db import models
from django.utils.encoding import python_2_unicode_compatible


from kasse.models import Profile
from stopwatch.models import TimeTrial


class NewsProfile(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    ignore = models.BooleanField(blank=True)

    @classmethod
    def get(cls, **kwargs):
        try:
            if sorted(kwargs.keys()) == ['profile'] and cls == NewsProfile:
                # Might be precomputed
                return kwargs['profile'].newsprofile
            else:
                return cls.objects.get(**kwargs)
        except cls.DoesNotExist:
            return cls(**kwargs)


class Config(models.Model):
    client_id = models.CharField(blank=True, max_length=100)
    app_secret = models.CharField(blank=True, max_length=100)
    app_access_token = models.TextField(blank=True)
    app_access_token_expiry = models.DateTimeField(blank=True, null=True)
    user_access_token = models.TextField(blank=True)
    user_access_token_expiry = models.DateTimeField(blank=True, null=True)
    page_access_token = models.TextField(blank=True)


@python_2_unicode_compatible
class Post(models.Model):
    post_time = models.DateTimeField(auto_now_add=True)
    fbid = models.CharField(max_length=50)
    text = models.TextField(blank=True)
    timetrials = models.ManyToManyField(TimeTrial)

    def __str__(self):
        try:
            page_id, post_id = self.fbid.split('_')
            return 'http://fb.com/%s/posts/%s' % (page_id, post_id)
        except:
            return '<Post %r>' % (sys.exc_info()[1],)


@python_2_unicode_compatible
class Comment(models.Model):
    post = models.ForeignKey(Post)
    post_time = models.DateTimeField(auto_now_add=True)
    fbid = models.CharField(max_length=50)
    text = models.TextField(blank=True)

    def __str__(self):
        try:
            post_id, comment_id = self.fbid.split('_')
            return '%s?comment_id=%s' % (self.post, comment_id)
        except:
            return '<Comment %r>' % (sys.exc_info()[1],)
