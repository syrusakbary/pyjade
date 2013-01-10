# -*- coding: utf-8 -*-

import contextlib

import pyjade
from pyjade.runtime import is_mapping


def process_param(key, value, terse=False):
    if terse:
        if (key == value) or (value is True):
            return key
    if isinstance(value, basestring):
        value = value.decode('utf8')
    return '''%s="%s"''' % (key, value)


TYPE_CODE = {
    'if': lambda v: bool(v),
    'unless': lambda v: not bool(v),
    'elsif': lambda v: bool(v),
    'else': lambda v: True}


@contextlib.contextmanager
def local_context_manager(compiler, local_context):
    old_local_context = compiler.local_context
    new_local_context = dict(compiler.local_context)
    new_local_context.update(local_context)
    compiler.local_context = new_local_context
    yield
    compiler.local_context = old_local_context


class HTMLCompiler(pyjade.compiler.Compiler):
    global_context = dict()
    local_context = dict()
    mixins = dict()
    useRuntime = True
    def _do_eval(self, value):
        if isinstance(value, basestring):
            value = value.encode('utf-8')
        try:
            value = eval(value, self.global_context, self.local_context)
        except:
            return ''
        return value

    def _get_value(self, attr):
        value = attr['val']
        if attr['static']:
            return attr['val']
        if isinstance(value, basestring):
            return self._do_eval(value)
        else:
            return attr['name']

    def _make_mixin(self, mixin):
        arg_names = [arg.strip() for arg in mixin.args.split(",")]
        def _mixin(self, args):
            if args:
                arg_values = self._do_eval(args)
            else:
                arg_values = []
            local_context = dict(zip(arg_names, arg_values))
            with local_context_manager(self, local_context):
                self.visitBlock(mixin.block)
        return _mixin

    def interpolate(self,text):
        return self._interpolate(text, lambda x: str(self._do_eval(x)))

    def visitInclude(self, node):
        raise pyjade.exceptions.CurrentlyNotSupported()

    def visitExtends(self, node):
        raise pyjade.exceptions.CurrentlyNotSupported()

    def visitMixin(self, mixin):
        if mixin.block:
            self.mixins[mixin.name] = self._make_mixin(mixin)
        else:
            self.mixins[mixin.name](self, mixin.args)

    def visitAssignment(self, assignment):
        self.global_context[assignment.name] = eval(assignment.val)

    def visitConditional(self, conditional):
        if not conditional.sentence:
            value = False
        else:
            value = self._do_eval(conditional.sentence)
        if TYPE_CODE[conditional.type](value):
            self.visit(conditional.block)
        elif conditional.next:
            for item in conditional.next:
                self.visitConditional(item)

    def visitCode(self, code):
        if code.buffer:
            val = code.val.lstrip()
            val = self._do_eval(val)
            if code.escape:
                val = str(val).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            self.buf.append(val)
        if code.block:
            self.visit(code.block)
        if not code.buffer and not code.block:
            exec code.val.lstrip() in self.global_context, self.local_context

    def visitEach(self, each):
        # Jade only allows javascript-style (key, value) or (item, index) iteration
        # Should validate that keys has at most two items, or else it's getting
        # into non-standard python-unpacking behavior.
        if len(each.keys) > 2:
            raise Exception('too many loop variables: %s'%','.join(each.keys))

        obj = self._do_eval(each.obj)

        # if it's a dict, we can keep both variables in the loop
        if is_mapping(obj):
            for item in obj:
                local_context = dict()
                if len(each.keys) > 1:
                    for (key, value) in zip(each.keys, item):
                        local_context[key] = value
                else:
                    local_context[each.keys[0]] = item
                with local_context_manager(self, local_context):
                    self.visit(each.block)

        # if it's not, then only if there's a second key, assign the loop index.
        else:
            for idx, item in enumerate(obj):
                local_context = dict()
                local_context[each.keys[0]] = item
                if len(each.keys) > 1:
                    local_context[each.keys[1]] = idx
                with local_context_manager(self, local_context):
                    self.visit(each.block)

    def attributes(self, attrs):
        return " ".join(['''%s="%s"''' % (k,v) for (k,v) in attrs.items()])

    def visitDynamicAttributes(self, attrs):
        classes = []
        params = []
        for attr in attrs:
            if attr['name'] == 'class':
                value = self._get_value(attr)
                if isinstance(value, list):
                    classes.extend(value)
                else:
                    classes.append(value)
            else:
                value = self._get_value(attr)

                if value not in (None,False):
                    params.append((attr['name'], value))
        if classes:
            classes = [unicode(c) for c in classes]
            params.append(('class', " ".join(classes)))
        if params:
            self.buf.append(" "+" ".join([process_param(k, v, self.terse) for (k,v) in params]))

def process_jade(src):
    parser = pyjade.parser.Parser(src)
    block = parser.parse()
    compiler = HTMLCompiler(block, pretty=True)
    return compiler.compile()
