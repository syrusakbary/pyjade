from django.template import TemplateDoesNotExist
from django.template.loaders.filesystem import Loader as DjFSLoader
from django.template.loaders.app_directories import Loader as DjAppLoader

from pyjade import Root, Environment

class DjangoEnvironment(Environment):

    auto_close_tags = {'for':'endfor',
                    'if':'endif',
                    'ifchanged':'endifchanged',
                    'ifequal':'endifequal',
                    'ifnotequal':'endifnotequal',
                    'block':'endblock',
                    'filter':'endfilter',
                    'autoescape':'endautoescape',
                    'with':'endwith',
                    'blocktrans': 'endblocktrans',
                    'spaceless': 'endspaceless',
                    'comment': 'endcomment',
                    'cache': 'endcache',
                    'localize': 'endlocalize',
                    'compress': 'endcompress'}

    may_contain_tags = {'if':['else'], 
                   'ifchanged':['else'],
                   'ifequal':['else'],
                   'ifnotequal':['else'],
                   'for':['empty'], 
                   'with':['with']}

    code_tags = ('for','block','if','ifchanged','ifequal','ifnotequal','else','filter','with','while')

    def tag_begin(self,node):
        return '{%%%s%%}'%node.statement

    def tag_end(self,node):
        return '{%%%s%%}'%node.closetag

def preprocessor(source):
    return unicode(Root(source,env=DjangoEnvironment()))

class FSLoader(DjFSLoader):
    is_usable = True

    def load_template_source(self, template_name, template_dirs=None):
        data, fn = super(FSLoader, self) \
            .load_template_source(template_name, template_dirs)

        if not template_name.endswith('.jade'):
            return data, fn

        return preprocessor(data), fn
    load_template_source.is_usable = True

class AppLoader(DjAppLoader):
    is_usable = True

    def load_template_source(self, template_name, template_dirs=None):
        data, fn = super(AppLoader, self) \
            .load_template_source(template_name, template_dirs)

        if not template_name.endswith('.jade'):
            return data, fn

        return preprocessor(data), fn
    load_template_source.is_usable = True