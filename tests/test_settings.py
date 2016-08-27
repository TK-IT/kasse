from kasse.settings.common import *

SECRET_KEY = 'just.testing'
DEBUG = True
THUMBNAIL_DEBUG = True
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
FIXTURE_DIRS = [os.path.join(BASE_DIR, 'tests/fixtures/')]

for key, handler in LOGGING['handlers'].items():
    if 'filename' in handler:
        handler['filename'] = os.path.join(BASE_DIR, 'test_%s.log' % key)
