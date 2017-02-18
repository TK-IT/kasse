from django_assets import Bundle, register
from dukpy.webassets import CompileLess
from dukpy.webassets import BabelJS


js = Bundle('awesomplete/awesomplete.js',
            'kasse/awesomplete.js',
            filters='jsmin', output='gen/awesomplete.js')
register('awesomplete', js)

js = Bundle('stopwatch/stopwatch.es6',
            'picturefill.js',
            filters=(BabelJS, 'jsmin'), output='gen/stopwatch.js')
register('stopwatch', js)


css = Bundle('kasse/style.css',
             filters=(CompileLess,), output='gen/kasse.css')
register('kassestyle', css)
