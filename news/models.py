from django.db import models


from kasse.models import Profile


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


class Post(models.Model):
    post_time = models.DateTimeField(auto_now_add=True)
    fbid = models.CharField(max_length=50)
    text = models.TextField(blank=True)


class Comment(models.Model):
    post = models.ForeignKey(Post)
    post_time = models.DateTimeField(auto_now_add=True)
    fbid = models.CharField(max_length=50)
    text = models.TextField(blank=True)
