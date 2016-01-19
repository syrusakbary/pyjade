# -*- coding: utf-8 -*-

import contextlib

import pyjade
from pyjade.runtime import is_mapping, iteration, escape
import six
import os
import operator

def process_param(key, value, terse=False):
    if terse:
        if (key == value) or (value is True):
            return key
    if isinstance(value, six.binary_type):
        value = value.decode('utf8')
    return '''%s="%s"''' % (key, value)


TYPE_CODE = {
    'if': operator.truth,
    'unless': operator.not_,
    'elsif': operator.truth,
    'else': lambda v: True}


@contextlib.contextmanager
def local_context_manager(compiler, local_context):
    old_local_context = compiler.local_context
    new_local_context = dict(compiler.local_context)
    new_local_context.update(local_context)
    compiler.local_context = new_local_context
    yield
    compiler.local_context = old_local_context


class Compiler(pyjade.compiler.Compiler):
    global_context = {}
    local_context = {}
    mixins = {}
    useRuntime = True
    def _do_eval(self, value):
        if isinstance(value, six.string_types):
            value = value.encode('utf-8')
        try:
            value = eval(value, self.global_context, self.local_context)
        except:
            return None
        return value

    def _get_value(self, attr):
        value = attr['val']
        if attr['static']:
            return attr['val']
        if isinstance(value, six.string_types):
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
            if not isinstance(arg_values, (list, tuple)):
                arg_values = [arg_values]
            local_context = dict(zip(arg_names, arg_values))
            with local_context_manager(self, local_context):
                self.visitBlock(mixin.block)
        return _mixin

    def interpolate(self, text, escape=True):
        return self._interpolate(text, lambda x: str(self._do_eval(x)))

    def visitInclude(self, node):
        if self.filename is not None:
            basepath = os.path.dirname(self.filename)
        else:
            basepath = os.getcwd()
        import_filename = os.path.join(basepath, node.path.strip('\"\''))

        if os.path.exists(import_filename):
            src = open(import_filename, 'r').read()
        elif os.path.exists("%s.jade" % import_filename):
            src = open("%s.jade" % import_filename, 'r').read()
        else:
            raise Exception("Include path doesn't exists: {}".format(import_filename))

        parser = pyjade.parser.Parser(src)
        block = parser.parse()
        self.visit(block)

    def visitExtends(self, node):
        raise pyjade.exceptions.CurrentlyNotSupported()

    def visitMixin(self, mixin):
        if mixin.block:
            self.mixins[mixin.name] = self._make_mixin(mixin)
        else:
            self.mixins[mixin.name](self, mixin.args)

    def visitAssignment(self, assignment):
        self.global_context[assignment.name] = self._do_eval(assignment.val)

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
            val = self.var_processor(val)
            val = self._do_eval(val)
            if code.escape:
                val = str(val).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            self.buf.append(val)
        if code.block:
            self.visit(code.block)
        if not code.buffer and not code.block:
            six.exec_(code.val.lstrip(), self.global_context, self.local_context)

    def visitEach(self, each):
        obj = iteration(self._do_eval(each.obj), len(each.keys))
        for item in obj:
            local_context = {}
            if len(each.keys) > 1:
                for (key, value) in zip(each.keys, item):
                    local_context[key] = value
            else:
                local_context[each.keys[0]] = item
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
                if value is True:
                    params.append((attr['name'], True))
                elif value not in (None,False):
                    params.append((attr['name'], escape(value)))
        if classes:
            classes = [six.text_type(c) for c in classes]
            params.append(('class', " ".join(classes)))
        if params:
            self.buf.append(" "+" ".join([process_param(k, v, self.terse) for (k,v) in params]))

HTMLCompiler = Compiler

def process_jade(src, filename=None):
    parser = pyjade.parser.Parser(src)
    block = parser.parse()
    compiler = Compiler(block, pretty=True)
    compiler.filename = filename
    return compiler.compile()
