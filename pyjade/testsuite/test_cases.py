import pyjade
import pyjade.ext.html
from pyjade.utils import process
from pyjade.exceptions import CurrentlyNotSupported

from nose import with_setup

processors =  {}
jinja_env = None

def teardown_func():
    pass


try:
    from jinja2 import Environment, FileSystemLoader
    from pyjade.ext.jinja import PyJadeExtension
    jinja_env = Environment(extensions=[PyJadeExtension],loader=FileSystemLoader('cases/'))
    def jinja_process (str):
        global jinja_env
        template = jinja_env.from_string(str)
        return template.render()

    processors['Jinja2'] = jinja_process
except ImportError:
    pass

try:
    import tornado.template
    from pyjade.ext.tornado import patch_tornado
    patch_tornado()

    loader = tornado.template.Loader('cases/')
    def tornado_process (str):
        global loader, tornado
        template = tornado.template.Template(str,name='_.jade',loader=loader)
        return template.generate().decode("utf-8")

    processors['Tornado'] = tornado_process
except ImportError:
    pass

try:
    from django.conf import settings
    settings.configure(
        TEMPLATE_DIRS=("cases/",),
        TEMPLATE_LOADERS = (
        ('pyjade.ext.django.Loader', (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),
        )
    )
    import django.template
    import django.template.loader
    from pyjade.ext.django import Compiler as DjangoCompiler

    def django_process(str):
        compiled = process(str,filename=None,compiler = DjangoCompiler)
        print compiled
        t = django.template.Template(compiled)

        ctx = django.template.Context()
        return t.render(ctx)

    processors['Django'] = django_process
except ImportError:
    pass

try:
    import pyjade.ext.mako
    import mako.template
    from mako.lookup import TemplateLookup
    dirlookup = TemplateLookup(directories=['cases/'],preprocessor=pyjade.ext.mako.preprocessor)

    def mako_process(str):
        t = mako.template.Template(str, lookup=dirlookup,preprocessor=pyjade.ext.mako.preprocessor, default_filters=['decode.utf8'])
        return t.render()

    processors['Mako'] = mako_process

except ImportError:
    pass

def setup_func():
    global jinja_env, processors


processors['Html'] = pyjade.ext.html.process_jade


def run_case(case,process):
    global processors
    process = processors[process]
    jade_file = open('cases/%s.jade'%case)
    jade_src = jade_file.read().decode('utf-8')
    jade_file.close()

    html_file = open('cases/%s.html'%case)
    html_src = html_file.read().strip('\n').decode('utf-8')
    html_file.close()
    try:
        processed_jade = process(jade_src).strip('\n')
        print 'PROCESSED\n',processed_jade,len(processed_jade)
        print 'EXPECTED\n',html_src,len(html_src)
        assert processed_jade==html_src

    except CurrentlyNotSupported:
        pass

exclusions = {
    'Html': set(['mixins', 'mixin.blocks', 'layout', 'unicode']),
    'Mako': set(['layout']),
    'Tornado': set(['layout']),
    'Jinja2': set(['layout']),
    'Django': set(['layout'])}

@with_setup(setup_func, teardown_func)
def test_case_generator():
    global processors

    import os
    for dirname, dirnames, filenames in os.walk('cases/'):
        # raise Exception(filenames)
        filenames = filter(lambda x:x.endswith('.jade'),filenames)
        filenames = map(lambda x:x.replace('.jade',''),filenames)
        for processor in processors.keys():
            for filename in filenames:
                if not filename in exclusions[processor]:
                    yield run_case, filename,processor
