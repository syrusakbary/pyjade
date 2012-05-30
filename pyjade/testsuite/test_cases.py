# import os
# import sys
# path = os.path.abspath(os.path.join(os.path.dirname(__file__),"../../"))
# sys.path.append(path)

import pyjade
from pyjade.exceptions import CurrentlyNotSupported
# from pyjade.ext.jinja import PyJadeExtension
processors =  {}
jinja_env = None
from nose import with_setup
# from pyjade import Parser, Compiler
# import unittest
# class PyjadeTestCase(unittest.TestCase):

#     ### use only these methods for testing.  If you need standard
#     ### unittest method, wrap them!

#     def setup(self):
#         pass

#     def test_files(self):
#       print 'a'
#     def teardown(self):
#         pass

# def suite():
#     suite = unittest.TestSuite()
#     suite.addTest(unittest.makeSuite(PyjadeTestCase))
#     return suite


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
except:
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
    import pyjade.ext.django

    def django_process(str):
        parser = pyjade.Parser(str,filename=None)
        block = parser.parse()
        compiler = pyjade.ext.django.Compiler(block)
        compiled = compiler.compile()
        print compiled
        t = django.template.Template(compiled)

        ctx = django.template.Context()
        return t.render(ctx)
        # for d in values:
        #     ctx.push()
        #     ctx.update(d)
        # t = django.template.loader.get_template(name)
        # t = pyjade.ext.django.Loader._process(str)
        # return t.render(ctx)

    processors['Django'] = django_process
except Exception,e:
    raise e

try:
    import pyjade.ext.mako
    import mako.template
    from mako.lookup import TemplateLookup
    dirlookup = TemplateLookup(directories=['cases/'],preprocessor=pyjade.ext.mako.preprocessor)

    def mako_process(str):
        
        # parser = pyjade.Parser(str,filename=None)
        # block = parser.parse()
        # compiler = pyjade.ext.mako.Compiler(block)
        # compiled = compiler.compile()
        # print compiled
        t = mako.template.Template(str, lookup=dirlookup,preprocessor=pyjade.ext.mako.preprocessor, default_filters=['decode.utf8'])
        return t.render()

    processors['Mako'] = mako_process

except Exception,e:
    raise e

def setup_func():
    global jinja_env, processors




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
                if filename == 'layout': continue #hack
                yield run_case, filename,processor

