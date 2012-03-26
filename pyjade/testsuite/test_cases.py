# import os
# import sys
# path = os.path.abspath(os.path.join(os.path.dirname(__file__),"../../"))
# sys.path.append(path)

import pyjade
from pyjade.ext.jinja import PyJadeExtension
# from pyjade.ext.jinja import PyJadeExtension

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

def setup_func():
    global env 
    from jinja2 import Environment, FileSystemLoader
    env = Environment(extensions=[PyJadeExtension],loader=FileSystemLoader('cases'))



def jinja_process (str):
    global env
    template = env.from_string(str)
    return template.render()


def run_case(case,process):
    jade_file = open('cases/%s.jade'%case)
    jade_src = jade_file.read().decode('utf-8')
    jade_file.close()

    html_file = open('cases/%s.html'%case)
    html_src = html_file.read().strip('\n').decode('utf-8')
    html_file.close()

    processed_jade = process(jade_src).strip('\n')
    print 'PROCESSED\n',processed_jade,len(processed_jade)
    print 'EXPECTED\n',html_src,len(html_src)
    assert processed_jade==html_src


@with_setup(setup_func, teardown_func)
def test_case_generator():

    import os
    for dirname, dirnames, filenames in os.walk('cases/'):
        # raise Exception(filenames)
        filenames = filter(lambda x:x.endswith('.jade'),filenames)
        filenames = map(lambda x:x.replace('.jade',''),filenames)

        for filename in filenames:
            if filename == 'layout': continue #hack
            yield run_case, filename,jinja_process

