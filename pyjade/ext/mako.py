import os
from pyjade import Parser, Compiler as _Compiler
from pyjade.runtime import attrs
from pyjade.utils import process
ATTRS_FUNC = '__pyjade_attrs'
IS_MAPPING_FUNC = '__pyjade_is_mapping'
class Compiler(_Compiler):
    useRuntime = True
    def compile_top(self):
        return '# -*- coding: utf-8 -*-\n<%%! from pyjade.runtime import attrs as %s, is_mapping as %s %%>'%(ATTRS_FUNC,IS_MAPPING_FUNC)

    def interpolate(self,text):
        return self._interpolate(text,lambda x:'${%s}'%x)

    def visitCodeBlock(self,block):
        if self.mixing > 0:
          self.buffer('${caller.body() if caller else ""}')
        else:
          self.buffer('<%%block name="%s">'%block.name)
          if block.mode=='append': self.buffer('${parent.%s()}'%block.name)
          self.visitBlock(block)
          if block.mode=='prepend': self.buffer('${parent.%s()}'%block.name)
          self.buffer('</%block>')

    def visitMixin(self,mixin):
        self.mixing += 1
        if not mixin.call:
          self.buffer('<%%def name="%s(%s)">'%(mixin.name,mixin.args)) 
          self.visitBlock(mixin.block)
          self.buffer('</%def>')
        elif mixin.block:
          self.buffer('<%%call expr="%s(%s)">'%(mixin.name,mixin.args))
          self.visitBlock(mixin.block)
          self.buffer('</%call>')
        else:
          self.buffer('${%s(%s)}'%(mixin.name,mixin.args))
        self.mixing -= 1

    def visitAssignment(self,assignment):
        self.buffer('<%% %s = %s %%>'%(assignment.name,assignment.val))

    def visitExtends(self,node):
        path = self.format_path(node.path)
        self.buffer('<%%inherit file="%s"/>'%(path))

    def visitInclude(self,node):
        path = self.format_path(node.path)
        self.buffer('<%%include file="%s"/>'%(path))


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


    def visitVar(self,var,escape=False):
        return '${%s%s}'%(var,'| h' if escape else '| n')

    def visitCode(self,code):
        if code.buffer:
            val = code.val.lstrip()
            self.buf.append(self.visitVar(val, code.escape))
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
        # Jade only allows javascript-style (key, value) or (item, index) iteration
        # Should validate that keys has at most two items, or else it's getting
        # into non-standard python-unpacking behavior.
        if len(each.keys) > 2:
            raise Exception('too many loop variables: %s'%','.join(each.keys))

        # if it's a dict, we can keep both variables in the loop
        self.buf.append('\\\n%% if %s(%s):\n'%(IS_MAPPING_FUNC,each.obj))
        self.buf.append('\\\n%% for %s in %s:\n'%(','.join(each.keys),each.obj))
        self.visit(each.block)
        self.buf.append('\\\n% endfor\n')

        # if it's not, then only if there's a second key, assign the loop index.
        self.buf.append('\\\n% else:\n')
        if len(each.keys) > 1:
            self.buf.append('\\\n%% for %s,%s in enumerate(%s):\n'%(each.keys[1],each.keys[0],each.obj))
        else:
            self.buf.append('\\\n%% for %s in %s:\n'%(each.keys[0],each.obj))
        self.visit(each.block)
        self.buf.append('\\\n% endfor\n')
        self.buf.append('\\\n% endif\n')

    def attributes(self,attrs):
        return "${%s(%s)}"%(ATTRS_FUNC,attrs)



def preprocessor(source):
    return process(source,compiler=Compiler)
