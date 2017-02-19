from django_assets import register
from dukpy.webassets import CompileLess
from dukpy.webassets import BabelJS


register('awesomplete',
         'awesomplete/awesomplete.js',
         'kasse/awesomplete.js',
         filters='jsmin', output='gen/awesomplete-%(version)s.js')

register('stopwatch',
         'stopwatch/stopwatch.es6',
         'picturefill.js',
         filters=(BabelJS, 'jsmin'), output='gen/stopwatch-%(version)s.js')

register('kassestyle',
         'kasse/style.css',
         filters=CompileLess, output='gen/kasse-%(version)s.css')
