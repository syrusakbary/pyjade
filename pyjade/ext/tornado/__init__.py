from pyjade import Compiler as _Compiler
from pyjade.runtime import attrs, escape, is_mapping
import tornado.template
from pyjade.utils import process
from pyjade.exceptions import CurrentlyNotSupported

ATTRS_FUNC = '__pyjade_attrs'
ESCAPE_FUNC = '__pyjade_escape'
IS_MAPPING_FUNC = '__pyjade_is_mapping'

class Compiler(_Compiler):
    def compile_top(self):
        return '{% autoescape None %}'
    def visitCodeBlock(self,block):
        self.buffer('{%% block %s %%}'%block.name)
        if block.mode=='append': self.buffer('{{super()}}')
        self.visitBlock(block)
        if block.mode=='prepend': self.buffer('{{super()}}')
        self.buffer('{% end %}')

    # def visitMixin(self,mixin):
    #     if mixin.block: 
    #       self.buffer('{%% macro %s(%s) %%}'%(mixin.name,mixin.args)) 
    #       self.visitBlock(mixin.block)
    #       self.buffer('{% end %}')
    #     else:
    #       self.buffer('{{%s(%s)}}'%(mixin.name,mixin.args))

    def visitMixin(self,mixin):
        raise CurrentlyNotSupported('mixin')

    def visitAssignment(self,assignment):
        self.buffer('{%% set %s = %s %%}'%(assignment.name,assignment.val))

    def visitCode(self,code):
        if code.buffer:
            val = code.val.lstrip()
            self.buf.append((('{{%s(%%s)}}'%ESCAPE_FUNC) if code.escape else '{{%s}}')%val)
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
        self.buf.append('{%% if %s(%s) %%}'%(IS_MAPPING_FUNC,each.obj))
        self.buf.append('{%% for %s in %s %%}'%(','.join(each.keys),each.obj))
        self.visit(each.block)
        self.buf.append('{% end %}')

        # if it's not, then only if there's a second key, assign the loop index.
        self.buf.append('{% else %}')
        if len(each.keys) > 1:
            self.buf.append('{%% for %s,%s in enumerate(%s) %%}'%(each.keys[1],each.keys[0],each.obj))
        else:
            self.buf.append('{%% for %s in %s %%}'%(each.keys[0],each.obj))
        self.visit(each.block)
        self.buf.append('{% end %}')
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
        return "{{%s(%s)}}"%(ATTRS_FUNC,attrs)

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
                IS_MAPPING_FUNC:is_mapping}
            )

# Patch tornado template engine for preprocess jade templates
def patch_tornado():
    tornado.template.Template = Template
