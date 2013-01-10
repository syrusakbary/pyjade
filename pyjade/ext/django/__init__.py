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
    useRuntime = True

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

    def visitEach(self,each):
        # Jade only allows javascript-style (key, value) or (item, index) iteration
        # Should validate that keys has at most two items, or else it's getting
        # into non-standard python-unpacking behavior.
        if len(each.keys) > 2:
            raise Exception('too many loop variables: %s'%','.join(each.keys))

        # if it's a dict, we can keep both variables in the loop
        self.buf.append('{%% if %s|__pyjade_is_mapping %%}'%each.obj)
        self.buf.append('{%% for %s in %s %%}'%(','.join(each.keys),each.obj))
        self.visit(each.block)
        self.buf.append('{% endfor %}')

        # if it's not, then only if there's a second key, assign the loop index.
        self.buf.append('{% else %}')
        self.buf.append('{%% for %s in %s %%}'%(each.keys[0],each.obj))
        if len(each.keys) > 1:
            # can't use __pyjade_set here, because it will try and evaluate
            # counter0 on a dict, even though we won't be in this block
            # in that case.
            self.buf.append('{%% with %s=forloop.counter0 %%}'%each.keys[1])
            self.visit(each.block)
            self.buf.append('{% endwith %}')
        else:
            self.visit(each.block)
        self.buf.append('{% endfor %}')
        self.buf.append('{% endif %}')

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