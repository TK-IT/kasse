from __future__ import absolute_import, unicode_literals, division


import hmac
import hashlib
import logging
import facebook

logger = logging.getLogger('news')


from news.models import Config, Post, Comment


FACEBOOK_API_VERSION = '2.12'


def ensure_valid_api_version():
    if FACEBOOK_API_VERSION not in facebook.VALID_API_VERSIONS:
        raise SystemExit('facebook-sdk %s does not support API version %s' %
                         (facebook.__version__, FACEBOOK_API_VERSION))


class ServiceUnavailable(Exception):
    def __init__(self):
        super().__init__("Service temporarily unavailable")


class GraphAPIWithSecretProof(facebook.GraphAPI):
    def __init__(self, *args, app_secret, **kwargs):
        super().__init__(*args, **kwargs)
        self.appsecret_proof = hmac.new(app_secret,
                                        self.access_token.encode('ascii'),
                                        hashlib.sha256).hexdigest().decode()

    def request(self, path, args=None, post_args=None, **kwargs):
        if post_args is not None:
            post_args['appsecret_proof'] = self.appsecret_proof
        return super().request(path, args, post_args=post_args, **kwargs)


def access_page():
    c = Config.objects.get()
    graph = GraphAPIWithSecretProof(c.page_access_token,
                                    version=FACEBOOK_API_VERSION,
                                    app_secret=c.app_secret)


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
