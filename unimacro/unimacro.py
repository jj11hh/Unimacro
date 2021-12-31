import os
from sys import stdout
from argparse import ArgumentParser
from .process_file import process_file
from .constants import *

def main():
    argparser = ArgumentParser(description="Unimacro preprocessor")
    argparser.add_argument("-b", "--tag-begin", default=DEFAULT_TAG_BEGIN, help="Tag begin")
    argparser.add_argument("-e", "--tag-end", default=DEFAULT_TAG_END, help="Tag end")
    argparser.add_argument("-s", "--strip", action="store_true", help="Strip out tags")
    
    group = argparser.add_mutually_exclusive_group()
    group.add_argument("-o", "--output", default=None, help="Output file")
    group.add_argument("-u", "--update", action="store_true", help="Update")

    argparser.add_argument("input", help="Input file")
    args = argparser.parse_args()

    if args.update:
        # we dont modify source files, but make a temp file to store the result
        output = open(args.input + ".tmp", "w")
    elif args.output is not None:
        output = open(args.output, "w")
    else:
        output = stdout

    with open(args.input) as io_stream:
        for line in process_file(io_stream, args.tag_begin, args.tag_end, args.strip):
            output.write(line)

    if output != stdout:
        output.close()
        
    if args.update:
        # replace the original file with the temp file
        os.replace(args.input + ".tmp", args.input[0])


if __name__ == "__main__":
    main()