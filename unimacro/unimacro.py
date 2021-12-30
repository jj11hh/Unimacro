import os
from sys import stdout
from argparse import ArgumentParser
from .process_file import process_file
from .constants import *

def main():
    argparser = ArgumentParser(description="Unimacro preprocessor")
    argparser.add_argument("-b", "--tag-begin", default=DEFAULT_TAG_BEGIN, help="Tag begin")
    argparser.add_argument("-e", "--tag-end", default=DEFAULT_TAG_END, help="Tag end")
    
    group = argparser.add_mutually_exclusive_group()
    group.add_argument("-o", "--output", default=None, help="Output file")
    group.add_argument("-u", "--update", action="store_true", help="Update")

    argparser.add_argument("input", nargs="+", help="Input file")
    args = argparser.parse_args()

    if args.update:
        output = open(args.input[0] + ".tmp", "w")
    elif args.output is not None:
        output = open(args.output, "w")
    else:
        output = stdout

    for input_file in args.input:
        with open(input_file) as io_stream:
            for line in process_file(io_stream, args.tag_begin, args.tag_end):
                output.write(line)

    if output != stdout:
        output.close()
        
    if args.update:
        os.replace(args.input[0] + ".tmp", args.input[0])


if __name__ == "__main__":
    main()