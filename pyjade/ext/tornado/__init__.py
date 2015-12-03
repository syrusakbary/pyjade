from pyjade import Compiler as _Compiler
from pyjade.runtime import attrs, escape, iteration
import tornado.template
from pyjade.utils import process
from pyjade.exceptions import CurrentlyNotSupported

ATTRS_FUNC = '__pyjade_attrs'
ESCAPE_FUNC = '__pyjade_escape'
ITER_FUNC = '__pyjade_iter'

class Compiler(_Compiler):

    def visitCodeBlock(self,block):
        self.buffer('{%% block %s %%}'%block.name)
        if block.mode=='append': self.buffer('{% raw super() %}')
        self.visitBlock(block)
        if block.mode=='prepend': self.buffer('{% raw super() %}')
        self.buffer('{% end %}')

    # def visitMixin(self,mixin):
    #     if mixin.block:
    #       self.buffer('{%% macro %s(%s) %%}'%(mixin.name,mixin.args))
    #       self.visitBlock(mixin.block)
    #       self.buffer('{% end %}')
    #     else:
    #       self.buffer('{%% raw %s(%s)} %%}'%(mixin.name,mixin.args))

    def interpolate(self, text, escape=True):
        return self._interpolate(text,lambda x:'{%% raw %s(%s) %%}' % (ESCAPE_FUNC, x))

    def visitMixin(self,mixin):
        raise CurrentlyNotSupported('mixin')

    def visitAssignment(self,assignment):
        self.buffer('{%% set %s = %s %%}'%(assignment.name,assignment.val))

    def visitCode(self,code):
        if code.buffer:
            val = code.val.lstrip()
            val = self.var_processor(val)
            if code.escape:
                self.buf.append('{%% raw %s(%s) %%}' % (ESCAPE_FUNC, val))
            else:
                self.buf.append('{%% raw %s %%}' % val)
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

    def visitEach(self,each):
        self.buf.append('{%% for %s in %s(%s,%s) %%}'%(','.join(each.keys),ITER_FUNC,each.obj,len(each.keys)))
        self.visit(each.block)
        self.buf.append('{% end %}')

    def visitConditional(self,conditional):
        TYPE_CODE = {
            'if': lambda x: 'if %s'%x,
            'unless': lambda x: 'if not %s'%x,
            'elif': lambda x: 'elif %s'%x,
            'else': lambda x: 'else'
        }
        self.buf.append('{%% %s %%}'%TYPE_CODE[conditional.type](conditional.sentence))
        if conditional.block:
            self.visit(conditional.block)
            for next in conditional.next:
              self.visitConditional(next)
        if conditional.type in ['if','unless']: self.buf.append('{% end %}')

    def attributes(self,attrs):
        return "{%% raw %s(%s) %%}" % (ATTRS_FUNC, attrs)

class Template(tornado.template.Template):
    def __init__(self, template_string, name="<string>", *args,**kwargs):
        is_jade = name.endswith(".jade")
        if is_jade:
            template_string = process(template_string,filename=name,compiler=Compiler)

        super(Template, self).__init__(template_string, name, *args,**kwargs)
        if is_jade:
            self.namespace.update(
                {ATTRS_FUNC:attrs,
                ESCAPE_FUNC:escape,
                ITER_FUNC:iteration}
            )

# Patch tornado template engine for preprocess jade templates
def patch_tornado():
    tornado.template.Template = Template
