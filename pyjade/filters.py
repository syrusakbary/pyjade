def _filter(text, text_filter, outer_indent, inner_indent):
    "Reformats text indentation for proper filtering, and processes it with the given 'text_filter' function."
    if len(outer_indent) >= 1:
        text = ''.join([line.replace(outer_indent+inner_indent, '',1)+'\n' for line in text.split('\n')])

    text = text_filter(text)
    return ''.join([outer_indent+line+'\n' for line in text.split('\n')])


def plain_filter(text, outer_indent='', inner_indent='  '):
    filter_function = lambda txt: txt
    return _filter(text, filter_function, outer_indent, inner_indent)


def cdata_filter(text, outer_indent='', inner_indent='  '):
    filter_function = lambda txt: '<![CDATA[\n' + txt + '\n]]>'
    return _filter(text, filter_function, outer_indent, inner_indent)


def markdown_filter(text, outer_indent='', inner_indent='  ', extensions=['extra']):
    try:
        from markdown import markdown
    except ImportError:
        raise ImportError("'markdown' module needed in order to filter markdown text. See: http://www.freewisdom.org/projects/python-markdown/Installation")

    filter_function = lambda txt: markdown(txt, extensions)
    return _filter(text, filter_function, outer_indent, inner_indent)


def rst_filter(text, outer_indent='', inner_indent='  ', overrides={}):
    from docutils.core import publish_parts

    filter_function = lambda txt: publish_parts(txt, writer_name='html', settings_overrides=overrides)['body']
    return _filter(text, filter_function, outer_indent, inner_indent)
