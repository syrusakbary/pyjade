from __future__ import absolute_import
from .lexer import Lexer
from . import nodes
import six

textOnly = ('script','style')

class Parser(object):
    def __init__(self,str,filename=None,**options):
        self.input = str
        self.lexer = Lexer(str,**options)
        self.filename = filename
        self.bloks = {}
        self.options = options
        self.contexts = [self]
        self.extending = False
        self._spaces = None
    
    def context(self,parser):
        if parser: self.context.append(parser)
        else: self.contexts.pop()

    def advance(self):
        return self.lexer.advance()

    def skip(self,n):
        while n>1: # > 0?
            self.advance()
            n -= 1

    def peek(self):
        p = self.lookahead(1)
        return p

    def line(self):
        return self.lexer.lineno

    def lookahead(self,n):
        return self.lexer.lookahead(n)

    def parse (self):
        block = nodes.Block()
        parser = None
        block.line = self.line()

        while 'eos' != self.peek().type:
            if 'newline' == self.peek().type: self.advance()
            else: block.append(self.parseExpr())

        parser = self.extending
        if parser:
            self.context(parser)
            ast = parser.parse()
            self.context()
            return ast

        return block

    def expect(self,type):
        t = self.peek().type
        if t == type: return self.advance()
        else:
            raise Exception('expected "%s" but got "%s" in file %s on line %d' %
                            (type, t, self.filename, self.line()))

    def accept(self,type):
        if self.peek().type == type: return self.advance()

    def parseExpr(self):
        t = self.peek().type
  
        if 'yield' == t:
            self.advance()
            block = nodes.Block()
            block._yield = True
            return block
        elif t in ('id','class'):
            tok = self.advance()
            self.lexer.defer(self.lexer.tok('tag','div'))
            self.lexer.defer(tok)
            return self.parseExpr()

        funcName = 'parse%s'%t.capitalize()
        if hasattr(self,funcName):
            return getattr(self,funcName)()
        else:
            raise Exception('unexpected token "%s" in file %s on line %d' %
                            (t, self.filename, self.line()))

    def parseText(self):
        tok = self.expect('text')
        node = nodes.Text(tok.val)
        node.line = self.line()
        return node

    def parseBlockExpansion(self):
        if ':'== self.peek().type:
            self.advance()
            return nodes.Block(self.parseExpr())
        else:
            return self.block()

    def parseAssignment(self):
        tok = self.expect('assignment')
        return nodes.Assignment(tok.name,tok.val)

    def parseCode(self):
        tok = self.expect('code')
        node = nodes.Code(tok.val,tok.buffer,tok.escape) #tok.escape
        block,i = None,1
        node.line = self.line()
        while self.lookahead(i) and 'newline'==self.lookahead(i).type:
            i+= 1
        block = 'indent' == self.lookahead(i).type
        if block:
            self.skip(i-1)
            node.block = self.block()
        return node

    def parseComment(self):
        tok = self.expect('comment')
        
        if 'indent'==self.peek().type:
            node = nodes.BlockComment(tok.val, self.block(), tok.buffer)
        else:
            node = nodes.Comment(tok.val,tok.buffer)
        
        node.line = self.line()
        return node

    def parseDoctype(self):
        tok = self.expect('doctype')
        node = nodes.Doctype(tok.val)
        node.line = self.line()
        return node

    def parseFilter(self):
        tok = self.expect('filter')
        attrs = self.accept('attrs')
        self.lexer.pipeless = True
        block = self.parseTextBlock()
        self.lexer.pipeless = False

        node = nodes.Filter(tok.val, block, attrs and attrs.attrs)
        node.line = self.line()
        return node

    def parseASTFilter(self):
        tok = self.expect('tag')
        attrs = self.accept('attrs')
        
        self.expect(':')
        block = self.block()

        node = nodes.Filter(tok.val, block, attrs and attrs.attrs)
        node.line = self.line()
        return node

    def parseEach(self):
        tok = self.expect('each')
        node = nodes.Each(tok.code, tok.keys)
        node.line = self.line()
        node.block = self.block()
        return node

    def parseConditional(self):
        tok = self.expect('conditional')
        node = nodes.Conditional(tok.val, tok.sentence)
        node.line = self.line()
        node.block = self.block()
        while True:
            t = self.peek()
            if 'conditional' == t.type and node.can_append(t.val):
                node.append(self.parseConditional())
            else:
                break
        return node

    def parseExtends(self):
        path = self.expect('extends').val.strip('"\'')
        return nodes.Extends(path)

    def parseCall(self):
        tok = self.expect('call')
        name = tok.val
        args = tok.args
        if args is None:
            args = ""
        block = self.block() if 'indent' == self.peek().type else None
        return nodes.Mixin(name,args,block,True)

    def parseMixin(self):
        tok = self.expect('mixin')
        name = tok.val
        args = tok.args
        if args is None:
            args = ""
        block = self.block() if 'indent' == self.peek().type else None
        return nodes.Mixin(name,args,block,block is None)

    def parseBlock(self):
        block = self.expect('block')
        mode = block.mode
        name = block.val.strip()
        block = self.block(cls=nodes.CodeBlock) if 'indent'==self.peek().type else nodes.CodeBlock(nodes.Literal(''))
        block.mode = mode
        block.name = name
        return block

    def parseInclude(self):
        path = self.expect('include').val.strip()
        return nodes.Include(path)

    def parseTextBlock(self):
        text = nodes.Text()
        text.line = self.line()
        spaces = self.expect('indent').val
        if not self._spaces: self._spaces = spaces
        indent = ' '*(spaces-self._spaces)
        while 'outdent' != self.peek().type:
            t = self.peek().type
            if 'newline'==t:
                text.append('\n')
                self.advance()
            elif 'indent'==t:
                text.append('\n')
                for node in self.parseTextBlock().nodes: text.append(node)
                text.append('\n')
            else:
                text.append(indent+self.advance().val)

        if spaces == self._spaces: self._spaces = None
        self.expect('outdent')
        return text

    def block(self,cls=nodes.Block):
        block = cls()
        block.line = self.line()
        self.expect('indent')
        while 'outdent' != self.peek().type:
            if 'newline'== self.peek().type:
                self.advance()
            else:
                block.append(self.parseExpr())
        self.expect('outdent')
        return block

    def parseTag(self):
        i = 2
        if 'attrs'==self.lookahead(i).type: i += 1
        if ':'==self.lookahead(i).type:
            if 'indent' == self.lookahead(i+1).type:
                return self.parseASTFilter

        name = self.advance().val
        tag = nodes.Tag(name)
        dot = None

        tag.line = self.line()

        while True:
            t = self.peek().type
            if t in ('id','class'):
                tok = self.advance()
                tag.setAttribute(tok.type,'"%s"'%tok.val,True)
                continue
            # if t=='id':
            #     tok = self.advance()
            #     tag.setId(tok.val)
            #     continue
            # elif t=='class':
            #     tok = self.advance()
            #     tag.addClass(tok.val)
            #     continue
            elif 'attrs'==t:
                tok = self.advance()
                for n,v in six.iteritems(tok.attrs):
                    tag.setAttribute(n,v,n in tok.static_attrs)
                continue
            else:
                break

        v = self.peek().val
        if '.'== v:
            dot = tag.textOnly = True
            self.advance()
        elif '<'== v: #For inline elements
            tag.inline = True
            self.advance()

        t = self.peek().type
        if 'text'==t: tag.text = self.parseText()
        elif 'code'==t: tag.code = self.parseCode()
        elif ':'==t:
            self.advance()
            tag.block = nodes.Block()
            tag.block.append(self.parseExpr())

        while 'newline' == self.peek().type: self.advance()
        
        tag.textOnly = tag.textOnly or tag.name in textOnly

        if 'script'== tag.name:
            type = tag.getAttribute('type')
            if not dot and type and 'text/javascript' !=type.strip('"\''): tag.textOnly = False

        if 'indent' == self.peek().type:
            if tag.textOnly:
                self.lexer.pipeless = True
                tag.block = self.parseTextBlock()
                self.lexer.pipeless = False
            else:
                block = self.block()
                if tag.block:
                    for node in block.nodes:
                        tag.block.append(node)
                else:
                    tag.block = block

        return tag
