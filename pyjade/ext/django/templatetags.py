# -*- coding: UTF-8 -*-

<<<<<<< HEAD
=======
from __future__ import unicode_literals

>>>>>>> 4c8d29a1f4c446aa933d170cee46fd896b59b52a
"""
A smarter {% if %} tag for django templates.

While retaining current Django functionality, it also handles equality,
greater than and less than operators. Some common case examples::

    {% if articles|length >= 5 %}...{% endif %}
    {% if "ifnotequal tag" != "beautiful" %}...{% endif %}
"""
import unittest
from django import template
from django.template import FilterExpression
from django.template.loader import get_template
import six

from pyjade.runtime import iteration

register = template.Library()

@register.tag(name="__pyjade_attrs")
def do_evaluate(parser, token):
  '''Calls an arbitrary method on an object.'''
  code = token.contents
  firstspace = code.find(' ')
  if firstspace >= 0:
    code = code[firstspace+1:]
  return Evaluator(code)

class Evaluator(template.Node):
  '''Calls an arbitrary method of an object'''
  def __init__(self, code):
    self.code = code

  def render(self, context):
    '''Evaluates the code in the page and returns the result'''
    modules = {
      'pyjade': __import__('pyjade')
    }
    context['false'] = False
    context['true'] = True
    try:
        result = unicode(eval('pyjade.runtime.attrs(%s)'%self.code,modules,context))
    except Exception as e:
        raise Exception('Eval error. Code was: %s' % self.code)
    return result

@register.tag(name="__pyjade_set")
def do_set(parser, token):
  '''Calls an arbitrary method on an object.'''
  code = token.contents
  firstspace = code.find(' ')
  if firstspace >= 0:
    code = code[firstspace+1:]
  return Setter(code)

class Setter(template.Node):
  '''Calls an arbitrary method of an object'''
  def __init__(self, code):
    self.code = code

  def render(self, context):
    '''Evaluates the code in the page and returns the result'''
    modules = {
    }
    context['false'] = False
    context['true'] = True
    new_ctx = eval('dict(%s)'%self.code,modules,context)
    context.update(new_ctx)
    return ''

register.filter('__pyjade_iter', iteration)



# Support for macros in Django, taken from https://gist.github.com/skyl/1715202
# Author: Skylar Saveland

def _setup_macros_dict(parser):
    ## Metadata of each macro are stored in a new attribute
    ## of 'parser' class. That way we can access it later
    ## in the template when processing 'usemacro' tags.
    try:
        ## Only try to access it to eventually trigger an exception
        parser._macros
    except AttributeError:
        parser._macros = {}


class DefineMacroNode(template.Node):
    def __init__(self, name, nodelist, args):

        self.name = name
        self.nodelist = nodelist
        self.args = []
        self.kwargs = {}
        for a in args:
            a = a.rstrip(',')
            if "=" not in a:
                self.args.append(a)
            else:
                name, value = a.split("=")
                self.kwargs[name] = value

    def render(self, context):
        ## empty string - {% macro %} tag does no output
        return ''


@register.tag(name="__pyjade_kwacro")
def do_macro(parser, token):
    try:
        args = token.split_contents()
        tag_name, macro_name, args = args[0], args[1], args[2:]
    except IndexError:
        m = ("'%s' tag requires at least one argument (macro name)"
            % token.contents.split()[0])
        raise template.TemplateSyntaxError(m)
    # TODO: could do some validations here,
    # for now, "blow your head clean off"
    nodelist = parser.parse(('end__pyjade_kwacro', ))
    parser.delete_first_token()

    ## Metadata of each macro are stored in a new attribute
    ## of 'parser' class. That way we can access it later
    ## in the template when processing 'usemacro' tags.
    _setup_macros_dict(parser)
    parser._macros[macro_name] = DefineMacroNode(macro_name, nodelist, args)
    return parser._macros[macro_name]


class LoadMacrosNode(template.Node):

    def __init__(self, file_name_expr, parser):
        self.file_name_expr = file_name_expr
        self.loaded = False

    def render(self, context):
        if not self.loaded:
            if not "_macros" in context:
                context["_macros"] = {}  # _setup_macros_dict_for_context(context)
            context["_macros"].update(self.load_macros(context))

        # empty string - {% loadmacros %} tag does no output
        return ''

    def load_macros(self, context, ignore_failures=False):
        try:
            file_name = self.file_name_expr.resolve(
                context,
                ignore_failures=True,
            )
        except template.VariableDoesNotExist:
            file_name = None

        if file_name is None:
            if ignore_failures:
                return None

            raise template.TemplateSyntaxError(
                "Unable to resolve file name: " + str(self.file_name_expr))

        t = get_template(file_name)
        macros = t.nodelist.get_nodes_by_type(DefineMacroNode)

        load_nodes = t.nodelist.get_nodes_by_type(LoadMacrosNode)
        others = [x.load_macros(context, ignore_failures) for x in load_nodes]

        own = {x.name: x for x in macros}

        result = {}
        for item in others:
            result.update(item)

        result.update(own)

        return result


@register.tag(name="__pyjade_loadkwacros")
def do_loadmacros(parser, token):
    try:
        tag_name, filename = token.split_contents()
    except IndexError:
        m = ("'%s' tag requires at least one argument (macro name)"
             % token.contents.split()[0])
        raise template.TemplateSyntaxError, m
    node = LoadMacrosNode(parser.compile_filter(filename), parser)
    preloaded_macros = node.load_macros({}, ignore_failures=True)
    if preloaded_macros:
        parser._macros = getattr(parser, "_macros", {})
        parser._macros.update(preloaded_macros)
        node.loaded = True

    return node


class UseMacroNode(template.Node):

    def __init__(self, macro, fe_args, fe_kwargs):
        self.macro = macro
        self.fe_args = fe_args
        self.fe_kwargs = fe_kwargs

    def render(self, context):

        for i, arg in enumerate(self.macro.args):
            try:
                fe = self.fe_args[i]
                context[arg] = fe.resolve(context)
            except IndexError:
                context[arg] = ""

        for name, default in six.iteritems(self.macro.kwargs):
            if name in self.fe_kwargs:
                context[name] = self.fe_kwargs[name].resolve(context)
            else:
                context[name] = FilterExpression(default,
                                                 self.macro.parser
                ).resolve(context)

        return self.macro.nodelist.render(context)


@register.tag(name="__pyjade_usekwacro")
def do_usemacro(parser, token):
    try:
        args = token.split_contents()
        tag_name, macro_name, values = args[0], args[1], args[2:]
    except IndexError:
        m = ("'%s' tag requires at least one argument (macro name)"
             % token.contents.split()[0])
        raise template.TemplateSyntaxError(m)
    try:
        macro = parser._macros[macro_name]
    except (AttributeError, KeyError):
        m = "Macro '%s' is not defined" % macro_name
        raise template.TemplateSyntaxError(m)

    fe_kwargs = {}
    fe_args = []

    for val in values:
        val = val.rstrip(',')
        if "=" in val:
            # kwarg
            name, value = val.split("=")
            fe_kwargs[name] = FilterExpression(value, parser)
        else:  # arg
            # no validation, go for it ...
            fe_args.append(FilterExpression(val, parser))

    macro.parser = parser
    return UseMacroNode(macro, fe_args, fe_kwargs)

if __name__ == '__main__':
    unittest.main()
