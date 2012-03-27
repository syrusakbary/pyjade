from jinja2.ext import Extension
import os
from pyjade import Parser, Compiler
from pyjade.runtime import attrs
ATTRS_FUNC = '__pyjade_attrs'
class JinjaCompiler(Compiler):
    def visitCodeBlock(self,block):
        self.buffer('{%% block %s %%}'%block.name)
        if block.mode=='prepend': self.buffer('{{super()}}')
        self.visitBlock(block)
        if block.mode=='append': self.buffer('{{super()}}')
        self.buffer('{% endblock %}')
    def visitMixin(self,mixin):
        if mixin.block: 
          self.buffer('{%% macro %s(%s) %%}'%(mixin.name,mixin.args)) 
          self.visitBlock(mixin.block)
          self.buffer('{% endmacro %}')
        else:
          self.buffer('{{%s(%s)}}'%(mixin.name,mixin.args))

    def visitAssignment(self,assignment):
        self.buffer('{%% set %s = %s %%}'%(assignment.name,assignment.val))

    def visitExtends(self,node):
        self.buffer('{%% extends "%s" %%}'%(node.path))

    def visitInclude(self,node):
        self.buffer('{%% include "%s" %%}'%(node.path))

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
        self.buf.append('{%% for %s in %s %%}'%(','.join(each.keys),each.obj))
        self.visit(each.block)
        self.buf.append('{% endfor %}')
    def attributes(self,attrs):
        return "{{%s(%s)}}"%(ATTRS_FUNC,attrs)


class PyJadeExtension(Extension):

    def __init__(self, environment):
        super(PyJadeExtension, self).__init__(environment)

        environment.extend(
            jade_file_extensions=('.jade',),
            # jade_env=JinjaEnvironment(),
        )
        environment.globals[ATTRS_FUNC] = attrs

    def preprocess(self, source, name, filename=None):
        if name and not os.path.splitext(name)[1] in self.environment.jade_file_extensions:
            return source

        parser = Parser(source,filename=name)
        block = parser.parse()
        compiler = JinjaCompiler(block)
        return compiler.compile()
        # procesed= process(source,name)
        # print procesed
        # return procesed