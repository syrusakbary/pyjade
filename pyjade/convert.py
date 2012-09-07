from pyjade.utils import process
def convert_file():
    import codecs
    aviable_compilers = {}
    try:
        from pyjade.ext.django import Compiler as DjancoCompiler
        aviable_compilers['django'] = DjancoCompiler
    except:
        pass
    try:
        from pyjade.ext.jinja import Compiler as JinjaCompiler
        aviable_compilers['jinja'] = JinjaCompiler
    except:
        pass
    try:
        from pyjade.ext.underscore import Compiler as UnderscoreCompiler
        aviable_compilers['underscore'] = UnderscoreCompiler
    except:
        pass
    try:
        from pyjade.ext.mako import Compiler as MakoCompiler
        aviable_compilers['mako'] = MakoCompiler
    except:
        pass
    from optparse import OptionParser
    usage = "usage: %prog [options] file [output]"
    parser = OptionParser(usage)
    parser.add_option("-o", "--output", dest="output",
                      help="write output to FILE", metavar="FILE")
    parser.add_option("-c", "--compiler", dest="compiler",
                        choices=['django', 'jinja', 'mako', 'underscore',],
                        default='django',
                        type="choice",
                      help="COMPILER must be django (default), jinja, underscore or mako ")
    # parser.add_option("-q", "--quiet",
    #                   action="store_false", dest="verbose", default=True,
    #                   help="don't print status messages to stdout")
    (options, args) = parser.parse_args()
    if len(args)<1:
        print "Specify the input file as the first argument."
        exit()
    file_output = options.output or (args[1] if len(args)>1 else None)
    compiler = options.compiler
    if compiler in aviable_compilers:
        template = codecs.open(args[0], 'r', encoding='utf-8').read()
        output = process(template,compiler=aviable_compilers[compiler])
        if file_output:
            outfile = codecs.open(file_output, 'w', encoding='utf-8')
            outfile.write(output)
        else:
            print output
    else:
        raise Exception('You must have %s installed!'%compiler)
    # print options,args

if __name__ == '__main__':
    convert_file()
