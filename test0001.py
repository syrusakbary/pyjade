import pyjade

from pyjade.ext.django.compiler import Compiler


with open('fun/files/test0001.jade') as f:
    src = f.read()
    parser = pyjade.Parser(src)
    block = parser.parse()
    compiler = Compiler(block)
    output = compiler.compile()
    print output
