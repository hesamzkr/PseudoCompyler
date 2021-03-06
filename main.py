from lex import *
from emit import *
from parse import *
import sys
import os


def main():
    print("\033[95mThe Pseudo-Pseudocode Compiler 😎\033[0m")

    if len(sys.argv) != 2:
        sys.exit("{color}Error\nCompiler needs source file as argument.{end}".format(
            color="\033[91m", end="\033[0m"))
    with open(sys.argv[1], 'r') as inputFile:
        input = inputFile.read()

    print("{color}Compiling...{end}".format(
        color="\033[94m", end="\033[0m"))

    lexer = Lexer(input)
    filename = sys.argv[1].split('.')[0]
    emitter = Emitter(f"{filename}.cs")
    parser = Parser(lexer, emitter)

    parser.program()
    emitter.writeFile()

    print("{color}Success{end}".format(
        color="\033[92m", end="\033[0m"))
    print("{color}Running...\n{end}".format(
        color="\033[93m", end="\033[0m"))

    os.system(f"csc -out:{filename}.exe {filename}.cs && {filename}.exe")


main()
