from jinja2.ext import Extension
import os
from pyjade import Parser, Compiler as _Compiler
from pyjade.runtime import attrs
from jinja2.debug import fake_exc_info
from pyjade.utils import process

ATTRS_FUNC = '__pyjade_attrs'
class Compiler(_Compiler):

    def visitCodeBlock(self,block):
        if self.mixing > 0:
          if self.mixing > 1:
            caller_name = '__pyjade_caller_%d' % self.mixing
          else:
            caller_name = 'caller'
          self.buffer('{%% if %s %%}{{ %s() }}{%% endif %%}' % (caller_name, caller_name))
        else:
          self.buffer('{%% block %s %%}'%block.name)
          if block.mode=='append': self.buffer('{{super()}}')
          self.visitBlock(block)
          if block.mode=='prepend': self.buffer('{{super()}}')
          self.buffer('{% endblock %}')

    def visitMixin(self,mixin):
        self.mixing += 1
        if not mixin.call:
          self.buffer('{%% macro %s(%s) %%}'%(mixin.name,mixin.args)) 
          self.visitBlock(mixin.block)
          self.buffer('{% endmacro %}')
        elif mixin.block:
          if self.mixing > 1:
            self.buffer('{%% set __pyjade_caller_%d=caller %%}' % self.mixing)
          self.buffer('{%% call %s(%s) %%}'%(mixin.name,mixin.args))
          self.visitBlock(mixin.block)
          self.buffer('{% endcall %}')
        else:
          self.buffer('{{%s(%s)}}'%(mixin.name,mixin.args))
        self.mixing -= 1

    def visitAssignment(self,assignment):
        self.buffer('{%% set %s = %s %%}'%(assignment.name,assignment.val))

    def visitCode(self,code):
        if code.buffer:
            val = code.val.lstrip()
            self.buf.append('{{%s%s}}'%(val,'|escape' if code.escape else ''))
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
        # Jade only allows javascript-style (key, value) or (item, index) iteration
        # Should validate that keys has at most two items, or else it's getting
        # into non-standard python-unpacking behavior.
        if len(each.keys) > 2:
            raise Exception('too many loop variables: %s'%','.join(each.keys))

        # if it's a dict, we can keep both variables in the loop
        self.buf.append('{%% if %s is mapping %%}'%each.obj)
        self.buf.append('{%% for %s in %s %%}'%(','.join(each.keys),each.obj))
        self.visit(each.block)
        self.buf.append('{% endfor %}')

        # if it's not, then only if there's a second key, assign the loop index.
        self.buf.append('{% else %}')
        self.buf.append('{%% for %s in %s %%}'%(each.keys[0],each.obj))
        if len(each.keys) > 1:
            self.buf.append('{%% set %s = loop.index0 %%}'%each.keys[1])
        self.visit(each.block)
        self.buf.append('{% endfor %}')
        self.buf.append('{% endif %}')

    def attributes(self,attrs):
        return "{{%s(%s)}}"%(ATTRS_FUNC,attrs)


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
    def __init__(self, environment):
        super(PyJadeExtension, self).__init__(environment)

        environment.extend(
            jade_file_extensions=('.jade',),
            # jade_env=JinjaEnvironment(),
        )
        # environment.exception_handler = self.exception_handler
        # get_corresponding_lineno
        environment.globals[ATTRS_FUNC] = attrs

    def preprocess(self, source, name, filename=None):
        if name and not os.path.splitext(name)[1] in self.environment.jade_file_extensions:
            return source
        return process(source,filename=name,compiler=Compiler)
