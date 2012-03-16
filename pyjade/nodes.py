from copy import copy
import re


class Node(object):
    only_text = False
    TYPE_RE = re.compile('^([\s]*)(!!!|doctype|//|[-=|%:]?)\s?(.*)$')

    def __init__(self, env, raw='', indent='', type=None, plain='', nested=False, **kwargs):
        self.children = []
        # print len(indent),raw,'a'
        self.env = env
        self.depth = len(indent)
        self._indent = indent
        self.raw = raw
        self.type = type
        self.plain = plain
        self._nested = nested
        self.globaldepth = 0

    def begin(self):
        return ''

    def end(self):
        return ''

    @property
    def nl(self):
        return self.env.nl or '\n'

    @property
    def indent(self):
        return  self.env.indent * self.globaldepth if self.env.indent else unicode(self._indent)

    @property
    def nested(self):
        return self._nested

    def content(self, printout=False):
        # p = self.nl if not self.nested else ''
        content = ''
        first = True

        # not sure what these stand for...
        p = False  # is parent node?
        r = False  # has remaining content?

        for child in self.children:
            # last = child==self.children[-1]
            if child.nested:
                if r and not first:
                    content += child.nl + child.indent
                content += unicode(child)

            else:
                content += (self.nl if not first else '') + unicode(child)
                p = True

            # Me Trying to decipher what the single-letter variable names stand for...
            if printout:
                print "NODE:"
                print self.plain
                print '+' * 28
                print "DEPTH =", self.depth, ", TYPE =", self.type, ", P =", p, ", R =", r, ", FIRST =", first, ", NESTED =", child.nested, ", CHILDREN =", len(child.children)
                print '-' * 28
                print content
                print '=' * 28
                print

            r = not child.nested
            first = False

        if p and not first:
            content += self.nl
            if not r:
                content += self.indent

        return content #+ ( (self.nl + (self.indent if not r else '') ) if p and not first  else '' )
        # return self.nl.join([unicode(child) for child in self.children])

    def output(self, begin, end):
        _begin = not (self.children and self.children[0].nested) and self.children
        _end = not (self.children and self.children[-1].nested) and self.children

        indent_begin = self.indent if (not self.nested and begin) else ''
        indent_finish = self.indent if (_end and end) else ''
        line_begin = self.nl if (_begin and begin) else ''
        # line_finish = self.nl if (_end and end) else ''
        return ''.join(
            (indent_begin, self.begin(), line_begin,
             self.content(),
             indent_finish, self.end())
        )

    def __str__(self):
        return self.output(True, True)

    def _should_insert_node(self, node):
        return self.inline_nl() and self.is_empty(node)

    def _should_go_inside_last_node(self, node=None, depth=None):
        depth = node.depth if depth == None else depth
        last = self.last

        return self.children and last and last.can_have_children() \
            and (
                last._should_insert_node(node)  \
                or depth > last.depth or (depth == last.depth and last.should_contain(node)))

    @staticmethod
    def is_empty(node):
        return isinstance(node, EmptyNode)

    last = None
    # @property
    # def non_empty_child(self):
    #     return filter(lambda x: not(self.is_empty(x)), self.children)
    # @property
    # def last (self):
    #     # return self.children[-1]
    #     try:
    #         return self.non_empty_child[-1]
    #     except:
    #         return None

    def last_children(self, depth):
        #self._should_go_inside_last_node(depth=depth)

        if self._should_go_inside_last_node(depth=depth):
            return self.last.last_children(depth)
        else:
            return self

        #return self.last.last_children(depth) \
        #    if self._should_go_inside_last_node(depth=depth)\
        #    else self

    def add(self, node):
        if not node:
            return
        if (self._should_go_inside_last_node(node)) and self.last:
            self.last.add(node)
        else:
            self.children.append(node)
            node.globaldepth = self.globaldepth + 1
            self.last = node if not self.is_empty(node) else self.last

    def create_node(self, plain, **kwargs):
        # if self._should_go_inside_last_node(): self.children[-1].create_node(string,**kwargs)
        kwargs['env'] = kwargs.get('env', self.env)
        kwargs['plain'] = plain

        if not plain.strip():
            if kwargs['env'].write_empty_lines:
                return EmptyNode(**kwargs)
            return None
        spaces, _type, content = self.TYPE_RE.match(plain).groups()
        spaces = kwargs.pop('indent', spaces)
        #content = kwargs.pop('raw',content)

        return self.last_children(len(spaces)).get_node(indent=spaces, type=_type, raw=content, **kwargs)

    def get_node(self, **kwargs):
        _type = kwargs.get('type', None)
        splitted = kwargs['raw'].strip().split(' ', 1)
        _type = _type or ('-' if splitted[0] in self.env.code_tags else _type)
        # try:
        if _type in ('%', ''):
            return HTMLNode(force=(_type == '%'), **kwargs)

        elif _type == '-':
            return TagNode(**kwargs)

        elif _type == '=':
            return VarNode(**kwargs)

        elif _type == '|':
            return MultiTextNode(**kwargs)

        elif _type == '//':
            return CommentNode(**kwargs)

        elif _type == ':':
            return FilterNode(**kwargs)

        elif _type in self.env.doctype_tags:
            return DoctypeNode(**kwargs)
        # except:
        #     pass
        return TextNode(**kwargs)

    def should_contain(self, node):
        return False

    def can_have_children(self):
        return False

    def inline_nl(self):
        return True


class Root(Node):
    def __init__(self, lines, **kwargs):
        super(Root, self).__init__(raw=lines, **kwargs)
        self.depth = None
        self.globaldepth = -1

        env_stack = [self.env]
        depth_stack = [0]
        for line in lines.splitlines():
            #if ':plain' in line:
            #    import pudb; pudb.set_trace()

            kwargs['env'] = env_stack[-1]
            new_node = self.create_node(line, **kwargs)

            if new_node and new_node.env is not env_stack[-1]:
                if new_node.depth > depth_stack[-1]:
                    env_stack.append(new_node.env)
                    depth_stack.append(new_node.depth)

                elif new_node.depth == depth_stack[-1]:
                    env_stack[-1] = new_node.env

            elif new_node and new_node.depth <= depth_stack[-1] and new_node.depth > 0:
                while new_node.depth <= depth_stack[-1] and depth_stack[-1] > 0:
                    env_stack.pop()
                    depth_stack.pop()
                #kwargs['env'] = env_stack[-1]
                #new_node = self.create_node(line, **kwargs)

            self.add(new_node)

    def can_have_children(self):
        return True

    def __str__(self):
        return self.content()


def equilibrate_parenthesis(string):
    par = 0
    es_st = False
    es_st2 = False
    a = iter(string)
    ant = False
    r = False
    for c in a:
        # print c, r
        b = es_st or es_st2
        if c == '"' and (not es_st2 and not r):
            es_st = not es_st
        elif c == "'" and (not es_st and not r):
            es_st2 = not es_st2
        elif not b:
            if c == '(':
                par += 1
            elif c == ')':
                par -= 1
        if par == 0:
            break
        ant, antc = c == '\\', ant
        if ant and not r:
            r = not r
        else:
            r = False
    ls = len(string)
    s = a.__length_hint__() or -ls
    if s == ls - 1:
        s = 0
    return string[:-s], string[-s:]


class HTMLNode(Node):
    # def __new__ (self,force,raw,**kwargs):
    #     if not force and raw[:raw.find(' ')] in AUTO_TAGS:
    #         return TagNode(raw=raw,**kwargs)
    #     return super(HTMLNode,self).__new__(self,raw=raw,**kwargs)
    RE = re.compile('^([\w#\-.\_]*)(.*)$')
    ATTR_RE = lambda attr: re.compile(r'''(%s\s*)(\s*(="([^"]*)")|\s*(='([^']*)')|\s*=(\S*)|(?=\s|$))''' % (attr))
    ATTR_CLASS_RE = ATTR_RE('class')
    ATTR_ID_RE = ATTR_RE('id')
    TAG_CLASS_ID = re.compile(r'([\.#])')

    def __init__(self, force=False, *args, **kwargs):
        super(HTMLNode, self).__init__(*args, **kwargs)

        completetag, sec = self.RE.match(self.raw).groups()
        # _,self.attributes,child_type,child_raw
        self.attributes, child = equilibrate_parenthesis(sec)
        self.attributes = self.attributes.strip('()')
        self.attributes = self.replace_var_attrs()
        child_type = child and child[0].strip()
        if child_type == '!':
            child_type = child[:2].strip()
        child_raw = child and child[len(child_type) + 1:]

        tag_splitted = self.TAG_CLASS_ID.split(completetag)
        self.tag = tag_splitted.pop(0) or self.env.html_default
        self.only_text = child_type == '.' or self.tag in self.env.html_plain_text

        parts = zip(tag_splitted[0::2], tag_splitted[1::2])
        self.tag_class = []
        self.tag_id = []

        for type_, value in parts:
            if type_ == '.':
                self.tag_class.append(value)
            elif type_ == '#':
                self.tag_id.append(value)

        self.attributes, changes_class = self.ATTR_CLASS_RE.subn(self.replace_class_attrs, self.attributes or '')
        self.attributes, changes_id = self.ATTR_ID_RE.subn(self.replace_id_attrs, self.attributes or '')
        # print child_type,self.only_text, self.tag

        if self.tag_class and not changes_class:
            self.attributes = self._print_attr('class', '"', ' '.join(self.tag_class)) + ((' ' + self.attributes) if self.attributes else '')

        if self.tag_id and not changes_id:
            self.attributes = self._print_attr('id', '"', ' '.join(self.tag_id)) + ((' ' + self.attributes) if self.attributes else '')

        if child_raw:
            if child_type == ':':
                self.add(self.create_node(plain=child_raw, indent=self.indent, nested=True, env=self.env))

            elif child_type == '=':
                self.add(VarNode(nested=True, raw=child_raw, env=self.env))
            elif child_type == '!=':
                self.add(VarNode(nested=True, raw=child_raw, env=self.env, escape=False))
            else:
                self.add(TextNode(raw=child_raw, nested=True, env=self.env))

        self._nested |= self.tag in self.env.html_inline
        self.self_close = child_type == '/' or self.tag in self.env.html_self_close

    class AttrNode(object):
        raw = None
        escape = True

    def replace_var_attrs(self):
        attr_array = self.attributes.split(',')
        for attr_key in range(0, len(attr_array)):
            pair = attr_array[attr_key].strip().split('=')
            if len(pair) < 2:
                continue

            name = pair[0].strip()
            value = pair[1].strip()

            if value == '':
                continue
            if not value.startswith('"') and not value.endswith('"') and not value.startswith("'") and not value.endswith("'"):
                attr_node = HTMLNode.AttrNode()
                attr_node.raw = value
                value = self.env.var(attr_node)
                if name.endswith('?'):
                    attr_str = name[:-1] + '="' + value + '"'
                    attr_str = '{% if ' + value.strip('{}') + ' %} ' + attr_str + '{% endif %}'
                else:
                    attr_str = name + '="' + value + '"'
                attr_array[attr_key] = attr_str

        res = ' '.join(i for i in attr_array if '{%' not in i)
        res += ''.join(i for i in attr_array if '{%' in i)
        return res

    def replace_attrs(self, match):
        attr = match.group(1)
        delim = (match.group(3) or match.group(5) or '="')[1]
        value = match.group(4) or match.group(6) or match.group(7)
        return attr, delim, value

    def replace_class_attrs(self, match):
        attr, delim, value = self.replace_attrs(match)
        value = ' '.join(self.tag_class + [value])
        return self._print_attr(attr, delim, value)

    def replace_id_attrs(self, match):
        attr, delim, value = self.replace_attrs(match)
        value = '_'.join(self.tag_id + [value])
        return self._print_attr(attr, delim, value)

    def _print_attr(self, attr, delim, value):
        return '%s=%s%s%s' % (attr, delim, value, delim)

    def begin(self):
        return '<%s>' % (' '.join((self.tag, self.attributes or '', '/' if self.self_close else ''))).strip()

    def end(self):
        return '' if self.self_close else '</%s>' % self.tag

    def can_have_children(self):
        return not self.self_close

    def get_node(self, **kwargs):
        if self.only_text:
            return PlainTextNode(**kwargs)
        return super(HTMLNode, self).get_node(**kwargs)

    def inline_nl(self):
        return (self.last and self.last.can_have_children() or not self.last)


class TagNode (Node):
    def __init__(self, **kwargs):
        super(TagNode, self).__init__(**kwargs)
        self.tag = self.raw.split(' ', 1)[0]
        self.statement = self.raw.strip()
        self.closetag = self.env.auto_close_tags.get(self.tag, None)
        # self.nested = True

    def begin(self):
        return self.env.tag_begin(self)

    def end(self):
        return self.env.tag_end(self)

    def should_contain(self, node):
        return isinstance(node, TagNode) and node.tag in self.env.may_contain_tags.get(self.tag, '')

    def can_have_children(self):
        return self.tag in self.env.auto_close_tags


class EmptyNode (Node):
    def __init__(self, **kwargs):
        super(EmptyNode, self).__init__(**kwargs)
        self.depth = None
        self._nested = False

    def __str__(self):
        return ''


class DoctypeNode(Node):
    def content(self):
        return self.env.doctypes.get(self.raw.strip().lower(), '<!DOCTYPE %s>' % self.raw.strip())


class TextNode (Node):
    def __str__(self):
        return self.indent + self.raw if not self.nested else self.raw


class PlainTextNode (Node):
    def __str__(self):
        return self.plain


class VarNode (TextNode):
    escape = True

    def __init__(self, escape=True, *args, **kwargs):
        super(TextNode, self).__init__(*args, **kwargs)
        self._nested = True
        self.escape = escape

    def __str__(self):
        return self.env.var(self)


class MultiTextNode (Node):
    def __init__(self, *args, **kwargs):
        super(MultiTextNode, self).__init__(*args, **kwargs)
        if self.raw:
            self.add(TextNode(env=self.env, raw=self.raw, nested=True, indent=self.indent))

    def can_have_children(self):
        return False

    def __str__(self):
        return self.output(True, self.nested)


class FilterNode (Node):
    def __init__(self, raw, *args, **kwargs):
        super(FilterNode, self).__init__(*args, **kwargs)
        self.filters = [self.get_filter(_filter) for _filter in raw.split(' ')]

        # Maintaining the original formatting of the text is important for certain filters
        self.env = copy(self.env)
        self.env.write_empty_lines = True

    def __str__(self):
        #self.indent+
        content = self.content()
        for name, _filter in reversed(self.filters):
            content = _filter(content, self.indent)
        return content
        #return reduce(lambda x, y: y(x), [self.content()]+list(reversed(self.filters)))
        #.replace(self.nl+self.indent,self.nl).replace(self.nl,self.nl+self.indent)

    def get_filter(self, name):
        if name in self.env.filters:
            return name, self.env.filters.get(name)
        else:
            raise Exception('Filter %s does not exist in the environment' % (name))

    def can_have_children(self):
        return True

    def get_node(self, **kwargs):
        return PlainTextNode(**kwargs)


class CommentNode(Node):
    def __init__(self, *args, **kwargs):
        super(CommentNode, self).__init__(*args, **kwargs)
        raw_content = self.raw.strip()

        self.conditional = raw_content and raw_content[0] == '['
        self.unbuffered = raw_content and raw_content[0] == '-'

        if self.raw:
            self.add(TextNode(env=self.env, raw=self.raw + ('>' if self.conditional else ''), nested=True, indent=self.indent))

    def can_have_children(self):
        return True

    def begin(self):
        return '<!-- ' if not self.conditional else '<!--'

    def end(self):
        return ' -->' if not self.conditional else '<![endif]-->'

    def output(self, begin, end):
        if self.unbuffered:
            return ''
        return super(CommentNode, self).output(begin, end)

    def __str__(self):
        return self.output(True, True)
