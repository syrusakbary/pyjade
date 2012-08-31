import logging
import os

from pyjade import Compiler as _Compiler, Parser
from pyjade.runtime import attrs
from pyjade.exceptions import CurrentlyNotSupported
from pyjade.utils import process

from django.conf import settings
from django.contrib.markup.templatetags.markup import markdown

class Compiler(_Compiler):
    autocloseCode = 'if,ifchanged,ifequal,ifnotequal,for,block,filter,autoescape,with,trans,blocktrans,spaceless,comment,cache,localize,compress'.split(',')

    def __init__(self, node, **options):
        if settings.configured:
            options.update(getattr(settings,'PYJADE',{}))
        filters = options.get('filters',{})
        if 'markdown' not in filters:
            filters['markdown'] = lambda x, y: markdown(x)        
        self.filters.update(filters)
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
        raise CurrentlyNotSupported('mixin')

    def visitCode(self,code):
        if code.buffer:
            val = code.val.lstrip()
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


from django import template
template.add_to_builtins('pyjade.ext.django.templatetags')

from django.utils.translation import trans_real

def decorate_templatize(func):
    def templatize(src, origin=None):
        html = process(src,compiler=Compiler)
        return func(html, origin)

    return templatize

trans_real.templatize = decorate_templatize(trans_real.templatize)

from loader import Loader