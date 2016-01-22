from __future__ import print_function
import pyjade
import pyjade.ext.html
from pyjade.utils import process
from pyjade.exceptions import CurrentlyNotSupported
import six
import os

from nose import with_setup

processors =  {}
jinja_env = None
cases_dir = os.path.join(os.path.dirname(__file__), 'cases') + '/'

def teardown_func():
    pass


try:
    from jinja2 import Environment, FileSystemLoader
    from pyjade.ext.jinja import PyJadeExtension
    jinja_env = Environment(extensions=[PyJadeExtension], loader=FileSystemLoader(cases_dir))
    def jinja_process (src, filename):
        global jinja_env
        template = jinja_env.get_template(filename)
        return template.render()

    processors['Jinja2'] = jinja_process
except ImportError:
    pass

# Test jinja2 with custom variable syntax: "{%#.-.** variable **.-.#%}"
try:
    from jinja2 import Environment, FileSystemLoader
    from pyjade.ext.jinja import PyJadeExtension
    jinja_env = Environment(extensions=[PyJadeExtension], loader=FileSystemLoader(cases_dir),
			variable_start_string = "{%#.-.**", variable_end_string="**.-.#%}"
    )
    def jinja_process_variable_start_string (src, filename):
        global jinja_env
        template = jinja_env.get_template(filename)
        return template.render()

    processors['Jinja2-variable_start_string'] = jinja_process_variable_start_string
except ImportError:
    pass

try:
    import tornado.template
    from pyjade.ext.tornado import patch_tornado
    patch_tornado()

    loader = tornado.template.Loader(cases_dir)
    def tornado_process (src, filename):
        global loader, tornado
        template = tornado.template.Template(src,name='_.jade',loader=loader)
        generated = template.generate(missing=None)
        if isinstance(generated, six.binary_type):
            generated = generated.decode("utf-8")
        return generated

    processors['Tornado'] = tornado_process
except ImportError:
    pass

try:
    import django
    from django.conf import settings

    template_dirs = [
        cases_dir,
        cases_dir + "include/django-include1",
        cases_dir + "include/django-include2",
    ]

    if django.VERSION >= (1, 8, 0):
        config = {
            'TEMPLATES': [{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': template_dirs,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                        'django.core.context_processors.request'
                    ],
                    'loaders': [
                        ('pyjade.ext.django.Loader', (
                            'django.template.loaders.filesystem.Loader',
                            'django.template.loaders.app_directories.Loader',
                        ))
                    ],
                },
            }]
        }
        if django.VERSION >= (1, 9, 0):
            config['TEMPLATES'][0]['OPTIONS']['builtins'] = ['pyjade.ext.django.templatetags']
    else:
        config = {
            'TEMPLATE_DIRS': tuple(template_dirs),
            'TEMPLATE_LOADERS': (
                ('pyjade.ext.django.Loader', (
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                )),
            )
        }

    settings.configure(**config)

    if django.VERSION >= (1, 7, 0):
        django.setup()

    import django.template
    import django.template.loader
    from pyjade.ext.django import Compiler as DjangoCompiler

    def django_process(src, filename):

        class PhonyObj(object):
            pass

        obj = PhonyObj()
        obj.pk = 99
        obj.site = 'www.pugjs.com'

        compiled = process(
            src,
            filename=cases_dir + filename.strip('\'\"'),
            compiler=DjangoCompiler,
            include_dirs=template_dirs
        )
        print(compiled)
        t = django.template.Template(compiled)

        ctx = django.template.Context()
        ctx['object'] = obj
        return t.render(ctx)

    processors['Django'] = django_process
except ImportError:
    raise

try:
    import pyjade.ext.mako
    import mako.template
    from mako.lookup import TemplateLookup
    dirlookup = TemplateLookup(
        directories=[cases_dir],
        preprocessor=pyjade.ext.mako.preprocessor
    )

    def mako_process(src, filename):
        t = mako.template.Template(src, lookup=dirlookup,preprocessor=pyjade.ext.mako.preprocessor, default_filters=['decode.utf8'])
        return t.render()

    processors['Mako'] = mako_process

except ImportError:
    pass

def setup_func():
    global jinja_env, processors

def html_process(src, filename):
    return pyjade.ext.html.process_jade(src, cases_dir + filename)

processors['Html'] = html_process

def run_case(case,process):
    global processors

    jade_filename = '%s.jade'%case
    case_filename = cases_dir + jade_filename

    processor = processors[process]
    jade_file = open(case_filename)
    jade_src = jade_file.read()
    if isinstance(jade_src, six.binary_type):
        jade_src = jade_src.decode('utf-8')
    jade_file.close()

    try:
        html_file = open(cases_dir + '%s-%s.html'%(case,process))
    except IOError:
        html_file = open(cases_dir + '%s.html'%(case))
    html_src = html_file.read().strip('\n')
    if isinstance(html_src, six.binary_type):
        html_src = html_src.decode('utf-8')
    html_file.close()
    processed_jade = processor(jade_src, jade_filename).strip('\n')
    print(
u'''
### PROCESSED (len=%d) ###
%s
### EXPECTED (len=%d) ###
%s
''' % (len(processed_jade), processed_jade, len(html_src), html_src)
        )
    assert processed_jade==html_src

exclusions = {
    'Html': set(['*-Django', 'inheritance', 'mixins', 'mixin.blocks', 'unicode']),
    'Mako': set(['*-Django']),
    'Tornado': set(['*-Django', 'interpolation', 'mixins', 'mixin.blocks']),
    'Jinja2': set(['*-Django']),
    'Jinja2-variable_start_string': set(['*-Django']),
    'Django': set(['mixin.blocks',])}


@with_setup(setup_func, teardown_func)
def test_case_generator():
    import os
    import sys

    global processors

    def fnmatchany(i, items):
        from fnmatch import fnmatch
        for exclusion in exclusions[processor]:
            if fnmatch(filename, exclusion):
                return True
        return False

    filenames = [
        os.path.splitext(i)[0]
        for i in os.listdir(cases_dir)
        if i.endswith('.jade')
    ]
    for processor in processors.keys():
        for filename in filenames:
            if fnmatchany(filename, exclusions[processor]):
                continue
            yield run_case, filename, processor
