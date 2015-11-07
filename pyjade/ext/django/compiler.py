import logging
import os

from pyjade import Compiler as _Compiler, Parser, register_filter
from pyjade.runtime import attrs
from pyjade.exceptions import CurrentlyNotSupported
from pyjade.utils import process

from django.conf import settings

class Compiler(_Compiler):
    autocloseCode = 'if,ifchanged,ifequal,ifnotequal,for,block,filter,autoescape,with,trans,blocktrans,spaceless,comment,cache,localize,compress,verbatim'.split(',')
    useRuntime = True

    def __init__(self, node, **options):
        if settings.configured:
            options.update(getattr(settings,'PYJADE',{}))
        super(Compiler, self).__init__(node, **options)

    def visitCodeBlock(self,block):
        self.buffer('{%% block %s %%}'%block.name)
        if block.mode=='append': self.buffer('{{block.super}}')
        self.visitBlock(block)
        if block.mode=='prepend': self.buffer('{{block.super}}')
        self.buffer('{% endblock %}')

    def visitAssignment(self,assignment):
        self.buffer('{%% __pyjade_set %s = %s %%}'%(assignment.name,assignment.val))

    def visitMixin(self,mixin):
        self.mixing += 1
        if not mixin.call:
          self.buffer('{%% __pyjade_kwacro %s %s %%}'%(mixin.name,mixin.args)) 
          self.visitBlock(mixin.block)
          self.buffer('{% end__pyjade_kwacro %}')
        elif mixin.block:
          raise CurrentlyNotSupported("The mixin blocks are not supported yet.")
        else:
          self.buffer('{%% __pyjade_usekwacro %s %s %%}'%(mixin.name,mixin.args))
        self.mixing -= 1

    def visitCode(self,code):
        if code.buffer:
            val = code.val.lstrip()
            val = self.var_processor(val)
            self.buf.append('{{%s%s}}'%(val,'|force_escape' if code.escape else ''))
        else:
            self.buf.append('{%% %s %%}'%code.val)

        if code.block:
            self.visit(code.block)

            if not code.buffer:
              codeTag = code.val.strip().split(' ',1)[0]
              if codeTag in self.autocloseCode:
                  self.buf.append('{%% end%s %%}'%codeTag)

    def attributes(self,attrs):
        return "{%% __pyjade_attrs %s %%}"%attrs


try:
    try:
        from django.template.base import add_to_builtins
    except ImportError: # Django < 1.8
        from django.template import add_to_builtins
    add_to_builtins('pyjade.ext.django.templatetags')
except ImportError:
    # Django 1.9 removed add_to_builtins and instead
    # provides a setting to specify builtins:
    # TEMPLATES['OPTIONS']['builtins'] = ['pyjade.ext.django.templatetags']
    pass

from django.utils.translation import trans_real

try:
    from django.utils.encoding import force_text as to_text
except ImportError:
    from django.utils.encoding import force_unicode as to_text

def decorate_templatize(func):
    def templatize(src, origin=None):
        src = to_text(src, settings.FILE_CHARSET)
        if origin.endswith(".jade"):
            html = process(src,compiler=Compiler)
        else:
            html = src
        return func(html, origin)

    return templatize

trans_real.templatize = decorate_templatize(trans_real.templatize)

try:
    from django.contrib.markup.templatetags.markup import markdown

    @register_filter('markdown')
    def markdown_filter(x,y):
        return markdown(x)
        
except ImportError:
    pass

