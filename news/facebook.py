from __future__ import absolute_import, unicode_literals, division


import facebook
import logging

logger = logging.getLogger('news')


from news.models import Config, Post, Comment


class ServiceUnavailable(Exception):
    def __init__(self):
        super().__init__("Service temporarily unavailable")


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


def comment_on_post(post, text, attachment=None):
    if not text:
        raise ValueError("Text must be non-empty")
    graph = access_page()
    data = dict(message=text)
    if attachment is not None:
        data['attachment_url'] = attachment
    try:
        o = graph.put_object(post.fbid, 'comments', **data)
    except facebook.GraphAPIError as exn:
        if str(exn) == '(#2) Service temporarily unavailable':
            raise ServiceUnavailable() from exn
        else:
            logger.exception("GraphAPIError while posting to /%s/comments %r",
                             post.fbid, data)
            raise
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
