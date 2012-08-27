from collections import deque

class Node(object):
	debug = False
	def __str__(self):
		return self.__dict__.__str__()
class BlockComment(Node):
	def __init__(self,val,block,buffer):
		self.block = block
		self.val = val
		self.buffer = buffer

class Block(Node):
	def __init__(self,node=None):
		self.nodes = deque()
		self.debug = False
		if node: self.append(node)

	def replace(self,other):
		other.nodes = self.nodes

	def append(self,node):
		return self.nodes.append(node)

	def prepend(self,node):
		return self.nodes.appendleft(node)

	def isEmpty(self):
		return bool(self.nodes)

	def unshift(self,node):
		return self.nodes.unshift(node)

class CodeBlock(Block): pass

class Code(Node):
	def __init__(self,val,buffer,escape):
		self.val = val
		self.block=None
		self.buffer = buffer
		self.escape = escape
class Comment(Node):
	def __init__(self,val,buffer):
		self.val = val
		self.buffer = buffer


class Doctype(Node):
	def __init__(self,val):
		self.val = val

class Each(Node):
	def __init__(self,obj, keys, block=None):
		self.obj = obj
		self.keys = keys
		self.block = block

class Assignment(Node):
	def __init__(self,name, val):
		self.name = name
		self.val = val

class Mixin(Node):
	def __init__(self,name, args, block=None):
		self.name = name
		self.args = args
		self.block = block

class Extends(Node):
	def __init__(self,path):
		self.path = path

class Include(Node):
	def __init__(self,path,extra=None):
		self.path = path
		self.extra = extra

class Conditional(Node):
	may_contain_tags = {'if': ['elif', 'else'],
						'for': ['else'],
						'elif': ['elif','else'],
						'unless': ['elif', 'else']}
	def __init__(self,type, sentence, block=None):
		self.type = type
		self.sentence = sentence
		self.block = block
		self.next = []
	def can_append(self,type):
		n = (self.next and self.next[-1].type) or self.type
		return type in self.may_contain_tags.get(n,[])
	def append(self,next):
		self.next.append(next)

class Filter(Node):
	def __init__(self,name, block, attrs):
		self.name = name
		self.block = block
		self.attrs = attrs
		self.isASTFilter = isinstance(block,Block)

class Literal(Node):
	def __init__(self,str):
		self.str = str.replace('\\','\\\\')

class Tag(Node):
	def __init__(self,name, block=None):
		self.name = name
		self.textOnly = False
		self.code = None
		self.text = None
		self.attrs = []
		self.block = block or Block()

	def setAttribute(self,name,val,static=True):
		self.attrs.append(dict(name=name,val=val,static=static))
		return self

	def removeAttribute(self,name):
		for attr in self.attrs:
			if attr and attr['name'] == name: self.attrs.remove(attr)

	def getAttribute(self,name):
		for attr in self.attrs:
			if attr and attr['name'] == name: return attr['val']

class Text(Node):
	def __init__(self, line=None):
		self.nodes = []
		if isinstance(line,basestring): self.append(line)

	def append(self,node):
		return self.nodes.append(node)