# from jinja2 import  TemplateSyntaxError
from jinja2.ext import Extension
from pyjade import Root, Environment
import os


class JinjaEnvironment(Environment):
    auto_close_tags = {'for': 'endfor',
                       'if': 'endif',
                       'block': 'endblock',
                       'filter': 'endfilter',
                       'autoescape': 'endautoescape',
                       'with': 'endwith',
                       'trans': 'endtrans',
                       'spaceless': 'endspaceless',
                       'comment': 'endcomment',
                       'cache': 'endcache',
                       'macro': 'endmacro',
                       'localize': 'endlocalize',
                       'compress': 'endcompress'}

    may_contain_tags = {'if': ['elif', 'else'],
                        'trans': ['pluralize'],
                        'for': ['empty'],
                        'with': ['with']}

    code_tags = ('include', 'extends', 'for', 'block', 'if', 'else', 'elif', 'filter', 'with', 'while', 'set', 'macro')

    def tag_begin(self, node):
        statement = node.statement
        if (statement.startswith('include') and
            '"' not in statement and '\'' not in statement):
            template_name = statement.split(' ', 1)[1]
            statement = 'include "%s.jade"' % template_name
        return '{%%%s%%}' % statement

    def tag_end(self, node):
        tag = ''
        if node.closetag:
            if node.statement[-1] == '-':
                tag = '-'
            tag = '{%%%s%%}' % (tag + node.closetag)

        return tag
        #return '{%% %s %%}' % (('-' if node.statement[-1]=='-' else '') + node.closetag) if node.closetag else ''

    def var(self, node):
        return '{{%s}}' % (node.raw)


class PyJadeExtension(Extension):

    def __init__(self, environment):
        super(PyJadeExtension, self).__init__(environment)

        environment.extend(
            jade_file_extensions=('.jade',),
            jade_env=JinjaEnvironment(),
        )

    def preprocess(self, source, name, filename=None):
        if name and not os.path.splitext(name)[1] in self.environment.jade_file_extensions:
            return source

        node = Root(source, env=self.environment.jade_env)
        # try:
        return unicode(node)
        # except TemplateIndentationError, e:
        #     raise TemplateSyntaxError(e.message, e.lineno, name=name, filename=filename)
        # except TemplateSyntaxError, e:
        #     raise TemplateSyntaxError(e.message, e.lineno, name=name, filename=filename)
