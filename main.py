from lex import *
from emit import *
from parse import *
import sys


def main():
    print("\033[95mPseudocode Compiler\033[0m")

    if len(sys.argv) != 2:
        sys.exit("{color}Error\nCompiler needs source file as argument.{end}".format(
            color="\033[91m", end="\033[0m"))
    with open(sys.argv[1], 'r') as inputFile:
        input = inputFile.read()

    lexer = Lexer(input)
    emitter = Emitter(f"{sys.argv[1].split('.')[0]}.cs")
    parser = Parser(lexer, emitter)

    parser.program()
    emitter.writeFile()
    print("{color}Compiling completed.{end}".format(
        color="\033[92m", end="\033[0m"))


main()
