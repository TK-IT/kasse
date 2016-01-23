from __future__ import absolute_import, unicode_literals, division


import facebook
import logging

logger = logging.getLogger('news')


from news.models import Config, Post, Comment


def access_page():
    c = Config.objects.get()
    return facebook.GraphAPI(c.page_access_token, version='2.5')


def access_user():
    c = Config.objects.get()
    return facebook.GraphAPI(c.user_access_token, version='2.5')


def new_post(text):
    graph = access_page()
    o = graph.put_object(
        parent_object='me', connection_name='feed',
        message=text)
    p = Post(fbid=o['id'], text=text)
    p.save()
    return p


def comment_on_post(post, text):
    graph = access_page()
    o = graph.put_comment(
        object_id=post.fbid,
        message=text)
    p = Comment(post=post, fbid=o['id'], text=text)
    p.save()
    return p


def comment_on_latest_post(text):
    p = Post.objects.all().order_by('-post_time')[0]
    return comment_on_post(p, text)


def edit_post(post, text):
    graph = access_page()
    graph.request(
        graph.version + '/' + post.fbid,
        post_args={'message': text},
        method='POST')
    post.text = text
    post.save()
