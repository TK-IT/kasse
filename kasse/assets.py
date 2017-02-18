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


#kasse/static
#├── awesomplete
#│   ├── awesomplete.css
#│   └── awesomplete.js
#├── chart.html
#├── favicon.ico
#└── kasse
#    ├── awesomplete.js
#    ├── favicon-152.png
#    └── style.css
#stopwatch/static
#├── picturefill.js
#└── stopwatch
#    ├── stopwatch.css
#    ├── stopwatch.es6
#    ├── stopwatch.js
#    ├── vaeske1080.jpg
#    ├── vaeske1280.jpg
#    ├── vaeske1440.jpg
#    ├── vaeske1920.jpg
#    ├── vaeske3256.jpg
#    ├── vaeske360.jpg
#    ├── vaeske640.jpg
#    └── vaeske720.jpg
#
#3 directories, 19 files
