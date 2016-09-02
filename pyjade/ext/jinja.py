from jinja2.ext import Extension
import os
import pyjade.runtime

from pyjade import Compiler as _Compiler
from pyjade.runtime import attrs as _attrs, iteration
from jinja2 import Markup
from jinja2.runtime import Undefined
from pyjade.utils import process

ATTRS_FUNC = '__pyjade_attrs'
ITER_FUNC = '__pyjade_iter'

def attrs(attrs, terse=False):
    return Markup(_attrs(attrs, terse, Undefined))

class Compiler(_Compiler):

    def visitCodeBlock(self,block):
        if self.mixing > 0:
          if self.mixing > 1:
            caller_name = '__pyjade_caller_%d' % self.mixing
          else:
            caller_name = 'caller'
          self.buffer(
            self.tag('if ' + caller_name) +
            self.variable(caller_name + '()') +
            self.tag('endif')
          )
        else:
          self.buffer(self.tag('block ' + block.name))
          if block.mode=='append': self.buffer(self.variable('super()'))
          self.visitBlock(block)
          if block.mode=='prepend': self.buffer(self.variable('super()'))
          self.buffer(self.tag('endblock'))

    def visitMixin(self,mixin):
        self.mixing += 1
        if not mixin.call:
          self.buffer(self.tag('macro %s(%s)'%(mixin.name,mixin.args)))
          self.visitBlock(mixin.block)
          self.buffer(self.tag('endmacro'))
        elif mixin.block:
          if self.mixing > 1:
            self.buffer(self.tag('set __pyjade_caller_%d=caller' % self.mixing))
          self.buffer(self.tag('call %s(%s)'%(mixin.name,mixin.args)))
          self.visitBlock(mixin.block)
          self.buffer(self.tag('endcall'))
        else:
          self.buffer(self.variable('%s(%s)' % (mixin.name, mixin.args)))
        self.mixing -= 1

    def visitAssignment(self,assignment):
        self.buffer(self.tag('set %s = %s'%(assignment.name,assignment.val)))

    def visitCode(self,code):
        if code.buffer:
            val = code.val.lstrip()
            val = self.var_processor(val)
            self.buf.append(self.variable(val + ('|escape' if code.escape else '')))
        else:
            self.buf.append(self.tag(code.val))

        if code.block:
            # if not code.buffer: self.buf.append('{')
            self.visit(code.block)
            # if not code.buffer: self.buf.append('}')

            if not code.buffer:
              codeTag = code.val.strip().split(' ',1)[0]
              if codeTag in self.autocloseCode:
                  self.buf.append(self.tag('end' + codeTag))

    def visitEach(self,each):
        self.buf.append(self.tag("for %s in %s(%s,%d)"%(','.join(each.keys),ITER_FUNC,each.obj,len(each.keys))))
        self.visit(each.block)
        self.buf.append(self.tag('endfor'))

    def attributes(self,attrs):
        return self.variable("%s(%s)" % (ATTRS_FUNC, attrs))


class PyJadeExtension(Extension):

    # def exception_handler(self,pt):
    #     # print '******************************'
    #     # print pt.exc_type
    #     # print pt.exc_value
    #     # print pt.frames[0].tb
    #     # line = pt.frames[0].tb.tb_lineno
    #     # pt.frames[0].tb.tb_lineno = line+10

    #     # print '******************************'
    #     _,_,tb = fake_exc_info((pt.exc_type,pt.exc_value, pt.frames[0].tb),'asfdasfdasdf',7)
    #     # pt.frames = [tb]
    #     raise pt.exc_type, pt.exc_value, tb
    options = {}
    file_extensions = '.jade'
    def __init__(self, environment):
        super(PyJadeExtension, self).__init__(environment)

        environment.extend(
            pyjade=self,
            # jade_env=JinjaEnvironment(),
        )

        # environment.exception_handler = self.exception_handler
        # get_corresponding_lineno
        environment.globals[ATTRS_FUNC] = attrs
        environment.globals[ITER_FUNC] = iteration
        self.variable_start_string = environment.variable_start_string
        self.variable_end_string = environment.variable_end_string
        self.options["block_start_string"] = environment.block_start_string
        self.options["block_end_string"] = environment.block_end_string
        self.options["variable_start_string"] = environment.variable_start_string
        self.options["variable_end_string"] = environment.variable_end_string

    def preprocess(self, source, name, filename=None):
        if (not name or
           (name and not os.path.splitext(name)[1] in self.file_extensions)):
            return source
        return process(source,filename=name,compiler=Compiler,**self.options)
