from django_assets import Bundle, register
from dukpy.webassets import CompileLess


js = Bundle('kasse/static/awesomplete/awesomplete.js',
            'kasse/static/kasse/awesomplete.js',
            filters='jsmin', output='gen/awesomplete.js')
register('awesomplete', js)

js = Bundle('stopwatch/static/stopwatch/stopwatch.js',
            'stopwatch/static/picturefill.js',
            filters='jsmin', output='gen/stopwatch.js')
register('stopwatch', js)


css = Bundle('kasse/static/kasse/style.css',
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
