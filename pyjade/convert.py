from __future__ import print_function
import sys
import logging
import codecs
import argparse
from pyjade.utils import process
import os

def convert_file():
    support_compilers_list = ['django', 'jinja', 'underscore', 'mako', 'tornado', 'html']
    available_compilers = {}
    for i in support_compilers_list:
        try:
            if i == "django":
                from django.conf import settings
                settings.configure()

            compiler_class = __import__('pyjade.ext.%s' % i, fromlist=['pyjade']).Compiler
        except ImportError as e:
            logging.warning(e)
        else:
            available_compilers[i] = compiler_class

    usage = "usage: %(prog)s [options] [input [output]]"
    parser = argparse.ArgumentParser(usage=usage)

    parser.add_argument("-o", "--output", help="write output to FILE", metavar="FILE")

    # use a default compiler here to sidestep making a particular
    # compiler absolutely necessary (ex. django)
    default_compiler = sorted(available_compilers.keys())[0]
    parser.add_argument("-c", "--compiler",
                    choices=list(available_compilers.keys()),
                    default=default_compiler,
                    metavar="COMPILER",
                    help="template compiler, %s by default; supported compilers are: %s" % (default_compiler, ", ".join(available_compilers.keys())))
    parser.add_argument("-e", "--ext", dest="extension",
                      help="set import/extends default file extension",
                      metavar="FILE")
    parser.add_argument("--block_start_string", metavar="STRING", default="{%", help="valid for jinja compiler only, defaut is '{%%'")
    parser.add_argument("--block_end_string", metavar="STRING", default="%}", help="valid for jinja compiler only, defaut is '%%}'")
    parser.add_argument("--variable_start_string", metavar="STRING", default="{{", help="valid for jinja compiler only, defaut is '{{'")
    parser.add_argument("--variable_end_string", metavar="STRING", default="}}", help="valid for jinja compiler only, defaut is '}}'")
    parser.add_argument("input", nargs="?")
    parser.add_argument("output", nargs="?", default=argparse.SUPPRESS)

    args = parser.parse_args()

    compiler = args.compiler

    if args.extension:
        extension = '.%s' % args.extension
    elif args.output:
        extension = os.path.splitext(args.output)[1]
    else:
        extension = None

    if compiler in available_compilers:
        import six
        if args.input:
            template = codecs.open(args.input, 'r', encoding='utf-8').read()
        elif six.PY3:
            template = sys.stdin.read()
        else:
            template = codecs.getreader('utf-8')(sys.stdin).read()

        output = process(template, compiler=available_compilers[compiler],
                         staticAttrs=True, extension=extension,
                         block_start_string=args.block_start_string,
                         block_end_string=args.block_end_string,
                         variable_start_string=args.variable_start_string,
                         variable_end_string=args.variable_end_string)

        if args.output:
            outfile = codecs.open(args.output, 'w', encoding='utf-8')
            outfile.write(output)
        elif six.PY3:
            sys.stdout.write(output)
        else:
            codecs.getwriter('utf-8')(sys.stdout).write(output)
    else:
        raise Exception('You must have %s installed!' % compiler)

if __name__ == '__main__':
    convert_file()
