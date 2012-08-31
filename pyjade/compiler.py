import re

class Compiler(object):
    RE_INTERPOLATE = re.compile(r'(\\)?([#!]){(.*?)}')
    doctypes = {
        '5': '<!DOCTYPE html>'
      , 'xml': '<?xml version="1.0" encoding="utf-8" ?>'
      , 'default': '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
      , 'transitional': '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
      , 'strict': '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
      , 'frameset': '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">'
      , '1.1': '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">'
      , 'basic': '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML Basic 1.1//EN" "http://www.w3.org/TR/xhtml-basic/xhtml-basic11.dtd">'
      , 'mobile': '<!DOCTYPE html PUBLIC "-//WAPFORUM//DTD XHTML Mobile 1.2//EN" "http://www.openmobilealliance.org/tech/DTD/xhtml-mobile12.dtd">'
    }
    inlineTags = [
        'a'
      , 'abbr'
      , 'acronym'
      , 'b'
      , 'br'
      , 'code'
      , 'em'
      , 'font'
      , 'i'
      , 'img'
      , 'ins'
      , 'kbd'
      , 'map'
      , 'samp'
      , 'small'
      , 'span'
      , 'strong'
      , 'sub'
      , 'sup'
      , 'textarea'
    ]
    selfClosing = [
        'meta'
      , 'img'
      , 'link'
      , 'input'
      , 'area'
      , 'base'
      , 'col'
      , 'br'
      , 'hr'
    ]
    autocloseCode = 'if,for,block,filter,autoescape,with,trans,spaceless,comment,cache,macro,localize,compress'.split(',')
    
    filters = {
        'cdata':lambda x,y:'<![CDATA[\n%s\n]]>'%x
    }

    def __init__(self,node,**options):
        self.options = options
        self.node = node
        self.hasCompiledDoctype = False
        self.hasCompiledTag = False
        self.pp = options.get('pretty',True)
        self.debug = options.get('compileDebug',False)!=False
        self.filters.update(options.get('filters',{}))
        self.doctypes.update(options.get('doctypes',{}))
        self.selfClosing.extend(options.get('selfClosing',[]))
        self.autocloseCode.extend(options.get('autocloseCode',[]))
        self.inlineTags.extend(options.get('inlineTags',[]))
        self.indents = 0
        self.doctype = None
        self.terse = False
        self.xml = False
        if 'doctype' in self.options: self.setDoctype(options['doctype'])

    def compile_top(self):
        return ''
    
    def compile(self):
        self.buf = [self.compile_top()]
        self.lastBufferedIdx = -1
        self.visit(self.node)
        return unicode(u''.join(self.buf))

    def setDoctype(self,name):
        self.doctype = self.doctypes.get(name or 'default','<!DOCTYPE %s>'%name)
        self.terse = name in ['5','html']
        self.xml = self.doctype.startswith('<?xml')

    def buffer (self,str):
        if self.lastBufferedIdx == len(self.buf):
            self.lastBuffered += str
            self.buf[self.lastBufferedIdx-1] = self.lastBuffered
        else:
            self.buf.append(str)
            self.lastBuffered = str;
            self.lastBufferedIdx = len(self.buf)

    def visit(self,node,*args,**kwargs):
        # debug = self.debug
        # if debug:
        #     self.buf.append('__jade.unshift({ lineno: %d, filename: %s });' % (node.line,('"%s"'%node.filename) if node.filename else '__jade[0].filename'));

        # if node.debug==False and self.debug:
        #     self.buf.pop()
        #     self.buf.pop()

        self.visitNode(node,*args,**kwargs)
        # if debug: self.buf.append('__jade.shift();')

    def visitNode (self,node,*args,**kwargs):
        name = node.__class__.__name__
        # print name, node
        return getattr(self,'visit%s'%name)(node,*args,**kwargs)

    def visitLiteral(self,node):
        self.buffer(node.str)

    def visitBlock(self,block):
        for node in block.nodes:
            self.visit(node)

    def visitCodeBlock(self,block):
        self.buffer('{%% block %s %%}'%block.name)
        if block.mode=='prepend': self.buffer('{{super()}}')
        self.visitBlock(block)
        if block.mode=='append': self.buffer('{{super()}}')
        self.buffer('{% endblock %}')

    def visitDoctype(self,doctype=None):
        if doctype  and (doctype.val or not self.doctype):
            self.setDoctype(doctype.val or 'default')

        if self.doctype: self.buffer(self.doctype)
        self.hasCompiledDoctype = True

    def visitMixin(self,mixin):
        if mixin.block: 
          self.buffer('{%% macro %s(%s) %%}'%(mixin.name,mixin.args)) 
          self.visitBlock(mixin.block)
          self.buffer('{% endmacro %}')
        else:
          self.buffer('{{%s(%s)}}'%(mixin.name,mixin.args))
    def visitTag(self,tag):
        self.indents += 1
        name = tag.name
        if not self.hasCompiledTag:
            if not self.hasCompiledDoctype and 'html'==name:
                self.visitDoctype()
            self.hasCompiledTag = True

        if self.pp and name not in self.inlineTags:
            self.buffer('\n'+'  '*(self.indents-1))

        closed = name in self.selfClosing and not self.xml
        self.buffer('<%s'%name)
        self.visitAttributes(tag.attrs)
        self.buffer('/>' if not self.terse and closed else '>')

        if not closed:
            if tag.code: self.visitCode(tag.code)
            if tag.text: self.buffer(self.interpolate(tag.text.nodes[0].lstrip()))
            self.escape = 'pre' == tag.name
            self.visit(tag.block)

            if self.pp and not name in self.inlineTags and not tag.textOnly:
                self.buffer('\n')

            if self.pp and (not name in self.inlineTags):
                self.buffer('  '*(self.indents-1))
            self.buffer('</%s>'%name)
        self.indents -= 1

    def visitFilter(self,filter):
        if filter.name not in self.filters:
          if filter.isASTFilter:
            raise Exception('unknown ast filter "%s:"'%filter.name)
          else:
            raise Exception('unknown filter "%s:"'%filter.name)

        fn = self.filters.get(filter.name)
        if filter.isASTFilter:
            self.buf.append(fn(filter.block,self,filter.attrs))
        else:
            text = ''.join(filter.block.nodes)
            text = self.interpolate(text)
            filter.attrs = filter.attrs or {}
            filter.attrs['filename'] = self.options.get('filename',None)
            self.buffer(fn(text,filter.attrs))

    def _interpolate(self,attr,repl):
        return self.RE_INTERPOLATE.sub(lambda matchobj:repl(matchobj.group(3)),attr)

    def interpolate(self,text):
        return self._interpolate(text,lambda x:'{{%s}}'%x)
 
    def visitText(self,text):
        text = ''.join(text.nodes)
        text = self.interpolate(text)
        self.buffer(text)
        self.buffer('\n')

    def visitComment(self,comment):
        if not comment.buffer: return
        if self.pp: self.buffer('\n'+'  '*(self.indents))
        self.buffer('<!--%s-->'%comment.val)

    def visitAssignment(self,assignment):
        self.buffer('{%% set %s = %s %%}'%(assignment.name,assignment.val))

    def visitExtends(self,node):
        self.buffer('{%% extends "%s" %%}'%(node.path))

    def visitInclude(self,node):
        self.buffer('{%% include "%s" %%}'%(node.path))

    def visitBlockComment(self,comment):
        if not comment.buffer: return
        isConditional = comment.val.strip().startswith('if')
        self.buffer('<!--[%s]>'%comment.val.strip() if isConditional else '<!--%s'%comment.val)
        self.visit(comment.block)
        self.buffer('<![endif]-->' if isConditional else '-->')

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
        if conditional.type in ['if','unless']: self.buf.append('{% endif %}')


    def visitCode(self,code):
        if code.buffer:
            val = code.val.lstrip()
            self.buf.append('{{%s%s}}'%(val,'|escape' if code.escape else ''))
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
        self.buf.append('{%% for %s in %s %%}'%(','.join(each.keys),each.obj))
        self.visit(each.block)
        self.buf.append('{% endfor %}')

    def attributes(self,attrs):
        return "{{__pyjade_attrs(%s)}}"%attrs

    def visitDynamicAttributes(self,attrs):
        buf,classes,params = [],[],{}
        terse='terse=True' if self.terse else ''
        for attr in attrs:
            if attr['name'] == 'class':
                classes.append('(%s)'%attr['val'])
            else:
                pair = "('%s',(%s))"%(attr['name'],attr['val'])
                buf.append(pair)

        if classes:
            classes = " , ".join(classes)
            buf.append("('class', (%s))"%classes)

        buf = ', '.join(buf)
        if self.terse: params['terse'] = 'True'
        if buf: params['attrs'] = '[%s]'%buf
        param_string = ', '.join(['%s=%s'%(n,v) for n,v in params.iteritems()])
        if buf or terse:
            self.buf.append(self.attributes(param_string))
    def visitAttributes(self,attrs):
        temp_attrs = []
        for attr in attrs:
            if attr['static']:
                if temp_attrs:
                    self.visitDynamicAttributes(temp_attrs)
                    temp_attrs = []
                self.buf.append(' %s=%s'%(attr['name'],attr['val']))
            else:
                temp_attrs.append(attr)
        
        if temp_attrs: self.visitDynamicAttributes(temp_attrs)

try:
    import coffeescript
    Compiler.filters['coffeescript'] = lambda x, y: '<script>%s</script>' % coffeescript.compile(x)
except ImportError:
    pass

try:
    import markdown
    Compiler.filters['markdown'] = lambda x,y: markdown.markdown(x, output_format='html5')
except ImportError:
    pass