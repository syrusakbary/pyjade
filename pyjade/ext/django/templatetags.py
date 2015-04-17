"""
A smarter {% if %} tag for django templates.

While retaining current Django functionality, it also handles equality,
greater than and less than operators. Some common case examples::

    {% if articles|length >= 5 %}...{% endif %}
    {% if "ifnotequal tag" != "beautiful" %}...{% endif %}
"""
import unittest
from django import template
try:
    from django.template.base import FilterExpression
except ImportError: # Django < 1.8
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
        return six.text_type(eval('pyjade.runtime.attrs(%s)'%self.code,modules,context))
    except NameError:
        return ''

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
    def render(self, context):
        ## empty string - {% loadmacros %} tag does no output
        return ''
 
 
@register.tag(name="__pyjade_loadkwacros")
def do_loadmacros(parser, token):
    try:
        tag_name, filename = token.split_contents()
    except IndexError:
        m = ("'%s' tag requires at least one argument (macro name)"
            % token.contents.split()[0])
        raise template.TemplateSyntaxError(m)
    if filename[0] in ('"', "'") and filename[-1] == filename[0]:
        filename = filename[1:-1]
    t = get_template(filename)
    macros = t.nodelist.get_nodes_by_type(DefineMacroNode)
    ## Metadata of each macro are stored in a new attribute
    ## of 'parser' class. That way we can access it later
    ## in the template when processing 'usemacro' tags.
    _setup_macros_dict(parser)
    for macro in macros:
        parser._macros[macro.name] = macro
    return LoadMacrosNode()
 
 
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
