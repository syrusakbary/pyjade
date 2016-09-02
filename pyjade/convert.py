from __future__ import print_function
import sys
import logging
import codecs
from optparse import OptionParser
from pyjade.utils import process
import os

def convert_file():
    support_compilers_list = ['django', 'jinja', 'underscore', 'mako', 'tornado', 'html']
    available_compilers = {}
    for i in support_compilers_list:
        try:
            compiler_class = __import__('pyjade.ext.%s' % i, fromlist=['pyjade']).Compiler
        except ImportError as e:
            logging.warning(e)
        else:
            available_compilers[i] = compiler_class

    usage = "usage: %prog [options] [file [output]]"
    parser = OptionParser(usage)
    parser.add_option("-o", "--output", dest="output",
                    help="Write output to FILE", metavar="FILE")
    # use a default compiler here to sidestep making a particular
    # compiler absolutely necessary (ex. django)
    default_compiler = sorted(available_compilers.keys())[0]
    parser.add_option("-c", "--compiler", dest="compiler",
                    choices=list(available_compilers.keys()),
                    default=default_compiler,
                    type="choice",
                    help=("COMPILER must be one of %s, default is %s" %
                          (', '.join(list(available_compilers.keys())), default_compiler)))
    parser.add_option("-e", "--ext", dest="extension",
                      help="Set import/extends default file extension",
                      metavar="FILE")

    parser.add_option("-r", "--recursive", action="store_true", dest="recursive",
                      help="Converts all files in this directory and subdirectories",metavar="DIRECTORY")

    options, args = parser.parse_args()

    file_output = options.output or (args[1] if len(args) > 1 else None)
    compiler = options.compiler
    recursive = options.recursive

    if options.extension:
        extension = '.%s' % options.extension
    elif options.output:
        extension = os.path.splitext(options.output)[1]
    else:
        extension = None

    if compiler in available_compilers:
        import six
        # do all the conversion first if its a file ...
        if len(args) >= 1:
            print(args)
            if os.path.isfile(args[0]): # checks if args[0] is a file.
                template = codecs.open(args[0], 'r', encoding='utf-8').read()
            elif six.PY3 and not os.path.isfile(args[0]) and not os.path.isdir(args[0]) :  # check if any arguments or flags was specified then read from std in if there wasnt.
                template = sys.stdin.read()
            elif os.path.isdir(args[0]):
                template = False
            elif os.path.isfile(args[0]) and not codecs.open(args[0], 'r', encoding='utf-8').read() : # input is a file but cant be read.
                try:
                    template = codecs.getreader('utf-8')(sys.stdin).read()
                except Exception as e:
                    print(e)
            if template: #usally gets here because of file or stdin was specified.
                output = process(template, compiler=available_compilers[compiler],staticAttrs=True, extension=extension)

        ### the rest of the output saves the pyjade output or does the converting now if its a folder.

        # do not call the walk directory routine if a dir is specified without the recursive ("-r") option.
        # "explicit is better than implicit" - The Zen Of Python.

        # lists all files in directories and lower subdirectories.
        # will raise "not a directory error" if user specifies a file or other.
        if recursive and os.path.isdir(args[0]):
            for root, dirs, files in os.walk(args[0], topdown=False):
                for name in files:
                    current_file_path = os.path.join(root, name) # returns full file path , for example: /home/user/stuff/example.jade
                    if "*.jade" not in current_file_path:
                    # could of done it inline with the walk - but i prefer readability.
                        pass
                    template = codecs.open(current_file_path, 'r', encoding='utf-8').read() # should only be a .jade file.

                    ### TODO - OUTPUT FILE EXTENSION VARIABLE
                    output_filepath = current_file_path[:current_file_path.rfind(".")] + ".html" # strips "jade" at the end of the path and replaces it with "html" which could be a variable in future.
                    # methods for each file in directory and all sub directories goes here.
                    output = process(template, compiler=available_compilers[compiler], staticAttrs=True, extension=extension)
                    outfile = codecs.open(output_filepath, 'w', encoding='utf-8')
                    outfile.write(output)

        # len(args) >= 1 added for debuging success conformation
        elif len(args) >= 1 and os.path.isdir(args[0]): # if path specified is a directory and has no -r option specified, then make sure the user wanted to do this.
            raise Exception("%s is a directory. \n Please use the '-r' flag if you want to convert a directory and all its subdirectories " % (args[0]))
        # len(args) >= 1 added for debuging success conformation
        elif len(args) >= 1 and os.path.isfile(args[0]): # if it gets to here without ending, then a single file or multiple explicit files were specified.
            # single file operations
            if file_output:  # will raise Exception "is not file" if its a directory or other - no really! inheritance!
                outfile = codecs.open(file_output, 'w', encoding='utf-8')
                outfile.write(output)
            elif six.PY3:
                sys.stdout.write(output)
            else:
                codecs.getwriter('utf-8')(sys.stdout).write(output)


    else:
        raise Exception('You must have %s installed!' % compiler)

if __name__ == '__main__':
    convert_file()
