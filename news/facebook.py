from __future__ import absolute_import, unicode_literals, division


import requests
import logging

logger = logging.getLogger('news')


from news.models import Config, Post, Comment


def new_post(text):
    c = Config.objects.get()
    page_id = '536317743199338'
    data = {
        'message': text,
        'access_token': c.page_access_token,
    }
    o = requests.post(
        'https://graph.facebook.com' +
        '/%s' % page_id +
        '/feed',
        data=data).json()
    try:
        post_id = o['id']
    except KeyError:
        logger.exception("%s", o)
        raise
    p = Post(fbid=post_id, text=text)
    p.save()
    return p


def comment_on_post(post, text):
    c = Config.objects.get()
    page_id = '536317743199338'
    post_id = post.fbid
    data = {
        'message': text,
        'access_token': c.page_access_token,
    }
    o = requests.post(
        'https://graph.facebook.com' +
        '/%s' % post_id +
        '/comments',
        data=data).json()
    comment_id = o['id']
    c = Comment(post=post, text=text, fbid=comment_id)
    c.save()
    return c


def comment_on_latest_post(text):
    p = Post.objects.all().order_by('-post_time')[0]
    return comment_on_post(p, text)
