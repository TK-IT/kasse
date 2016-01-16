from django.db import models


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
