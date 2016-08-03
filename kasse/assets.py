from django_assets import Bundle, register


js = Bundle('kasse/static/awesomplete/awesomplete.js',
            'kasse/static/kasse/awesomplete.js',
            filters='jsmin', output='gen/awesomplete.js')
register('awesomplete', js)

js = Bundle('stopwatch/static/stopwatch/stopwatch.js',
            'stopwatch/static/picturefill.js',
            filters='jsmin', output='gen/stopwatch.js')
register('stopwatch', js)


def less(in_, out, **kwargs):
    from dukpy.evaljs import evaljs
    return evaljs(
        '''
        var render = require('less/index.js').render;
        res = null;
        render(dukpy.less_input, function (err, output) {
            res = {err: err, output: output};
        });
        ''',
        less_input=in_.read())


css = Bundle('kasse/static/kasse/style.css',
             filters=(less,), output='gen/kasse.css')
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
