from lex import *
from emit import *
from parse import *
import sys


def main():
    print("Pseudocode Compiler")

    if len(sys.argv) != 2:
        sys.exit("Error: Compiler needs source file as argument.")
    with open(sys.argv[1], 'r') as inputFile:
        input = inputFile.read()

    lexer = Lexer(input)
    emitter = Emitter(f"{sys.argv[1].split('.')[0]}.cs")
    parser = Parser(lexer, emitter)

    parser.program()
    emitter.writeFile()
    print("Compiling completed.")


main()
