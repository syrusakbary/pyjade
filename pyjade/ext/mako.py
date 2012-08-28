import os
from pyjade import Parser, Compiler as _Compiler
from pyjade.runtime import attrs
from pyjade.utils import process
ATTRS_FUNC = '__pyjade_attrs'
class Compiler(_Compiler):
    def compile_top(self):
        return '# -*- coding: utf-8 -*-\n<%%! from pyjade.runtime import attrs as %s %%>'%ATTRS_FUNC

    def interpolate(self,text):
        return self._interpolate(text,lambda x:'${%s}'%x)

    def visitCodeBlock(self,block):
        self.buffer('<%%block name="%s">'%block.name)
        if block.mode=='append': self.buffer('${parent.%s()}'%block.name)
        self.visitBlock(block)
        if block.mode=='prepend': self.buffer('${parent.%s()}'%block.name)
        self.buffer('</%block>')
    def visitMixin(self,mixin):
        if mixin.block: 
          self.buffer('<%%def name="%s(%s)">'%(mixin.name,mixin.args)) 
          self.visitBlock(mixin.block)
          self.buffer('</%def>')
        else:
          self.buffer('${%s(%s)}'%(mixin.name,mixin.args))

    def visitAssignment(self,assignment):
        self.buffer('<%% %s = %s %%>'%(assignment.name,assignment.val))

    def visitExtends(self,node):
        self.buffer('<%%inherit file="%s"/>'%(node.path))

    def visitInclude(self,node):
        self.buffer('<%%include file="%s"/>'%(node.path))


    def visitConditional(self,conditional):
        TYPE_CODE = {
            'if': lambda x: 'if %s'%x,
            'unless': lambda x: 'if not %s'%x,
            'elif': lambda x: 'elif %s'%x,
            'else': lambda x: 'else'
        }
        self.buf.append('\\\n%% %s:\n'%TYPE_CODE[conditional.type](conditional.sentence))
        if conditional.block:
            self.visit(conditional.block)
            for next in conditional.next:
              self.visitConditional(next)
        if conditional.type in ['if','unless']: self.buf.append('\\\n% endif\n')


    def visitCode(self,code):
        if code.buffer:
            val = code.val.lstrip()
            self.buf.append('${%s%s}'%(val,'| h' if code.escape else '| n'))
        else:
            self.buf.append('<%% %s %%>'%code.val)

        if code.block:
            # if not code.buffer: self.buf.append('{')
            self.visit(code.block)
            # if not code.buffer: self.buf.append('}')

            if not code.buffer:
              codeTag = code.val.strip().split(' ',1)[0]
              if codeTag in self.autocloseCode:
                  self.buf.append('</%%%s>'%codeTag)
 
    def visitEach(self,each):
        self.buf.append('\\\n%% for %s in %s:\n'%(','.join(each.keys),each.obj))
        self.visit(each.block)
        self.buf.append('\\\n% endfor\n')
    def attributes(self,attrs):
        return "${%s(%s)}"%(ATTRS_FUNC,attrs)



def preprocessor(source):
    return process(source,compiler=Compiler)
