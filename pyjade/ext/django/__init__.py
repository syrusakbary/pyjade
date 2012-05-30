import os
from django.contrib.markup.templatetags.markup import markdown
from pyjade import Compiler as _Compiler, Parser
from pyjade.runtime import attrs
from pyjade.exceptions import CurrentlyNotSupported

class Compiler(_Compiler):
    autocloseCode = 'if,ifchanged,ifequal,ifnotequal,for,block,filter,autoescape,with,blocktrans,spaceless,comment,cache,localize,compress'.split(',')

    def __init__(self, node, **options):
        super(Compiler, self).__init__(node, **options)
        self.filters['markdown'] = lambda x, y: markdown(x)

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
            # if not code.buffer: self.buf.append('{')
            self.visit(code.block)
            # if not code.buffer: self.buf.append('}')

        if not code.buffer:
          codeTag = code.val.strip().split(' ',1)[0]
          if codeTag in self.autocloseCode:
              self.buf.append('{%% end%s %%}'%codeTag)

    def attributes(self,attrs):
        return "{%% __pyjade_attrs %s %%}"%attrs


from django import template
template.add_to_builtins('pyjade.ext.django.templatetags')

from loader import Loader