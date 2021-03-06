import sys
import re
from lex import *

# Parse translates tokens into C#, checks grammar and emits the code


class Parser:
    def __init__(self, lexer, emitter):
        self.lexer = lexer
        self.emitter = emitter

        self.symbols = set()  # All the declared variables

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken()    # Call this twice to initialize current and peek.

    def checkToken(self, kind):
        return kind == self.curToken.kind

    def checkPeek(self, kind):
        return kind == self.peekToken.kind

    # Check if they match, if not error. also go next token
    def match(self, kind):
        if not self.checkToken(kind):
            self.abort(
                f"Expected ({kind.name}), got ({self.curToken.kind.name}), text: {self.curToken.text}")
        self.nextToken()

    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()

    def isComparisonOperator(self):
        return self.checkToken(TokenType.GT) or self.checkToken(TokenType.GTEQ) or self.checkToken(TokenType.LT) or self.checkToken(TokenType.LTEQ) or self.checkToken(TokenType.EQEQ) or self.checkToken(TokenType.NOTEQ) or self.checkToken(TokenType.AND) or self.checkToken(TokenType.OR) or self.checkToken(TokenType.NOT)

    def abort(self, message):
        txt = "{color}Parse Error\n{message}{end}"
        sys.exit(txt.format(color="\033[91m", end="\033[0m", message=message))

    def program(self):
        self.emitter.headerLine(
            "using System;\nusing System.IO;\nusing System.Linq;\nusing System.Collections.Generic;\n")
        self.emitter.headerLine(
            "class Program\n{\n\tpublic static void Main(string[] args)\n\t{")

        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

        while not self.checkToken(TokenType.EOF):
            self.statement()

        self.emitter.emitLine("\t}")

    def statement(self):
        if self.checkToken(TokenType.PROCEDURE):
            self.nextToken()
            self.emitter.isMethod = True
            name = self.curToken.text
            if name not in self.symbols:
                self.symbols.add(name)
            else:
                self.abort(f"Procedure name ({name}) already exists")
            self.emitter.emit(f"public static void {name}(")
            self.match(TokenType.IDENT)
            self.match(TokenType.BRACKOPEN)

            while not self.checkToken(TokenType.BRACKCLOSE):
                parName = self.curToken.text
                if parName not in self.symbols:
                    self.symbols.add(parName)
                self.match(TokenType.IDENT)

                self.match(TokenType.COLON)
                dataType = self.typeConversion(self.curToken.text)
                self.emitter.emit(f"{dataType} {parName}")
                self.nextToken()
                if self.checkToken(TokenType.COMMA):
                    self.emitter.emit(", ")
                    self.nextToken()

            self.emitter.emitLine(")\n\t{")
            self.match(TokenType.BRACKCLOSE)

        elif self.checkToken(TokenType.FUNCTION):
            self.nextToken()
            self.emitter.isMethod = True
            name = self.curToken.text
            if name not in self.symbols:
                self.symbols.add(name)
            else:
                self.abort(f"Function name ({name}) already exists")
            self.match(TokenType.IDENT)
            self.match(TokenType.BRACKOPEN)

            parString = ""
            while not self.checkToken(TokenType.BRACKCLOSE):
                parName = self.curToken.text
                if parName not in self.symbols:
                    self.symbols.add(parName)
                self.match(TokenType.IDENT)

                self.match(TokenType.COLON)
                dataType = self.typeConversion(self.curToken.text)
                parString += f"{dataType} {parName}"
                self.nextToken()
                if self.checkToken(TokenType.COMMA):
                    parString += ", "
                    self.nextToken()

            self.match(TokenType.BRACKCLOSE)
            self.match(TokenType.RETURNS)
            returnsType = self.typeConversion(self.curToken.text)

            self.emitter.emitLine(
                f"public static {returnsType} {name}({parString}) " + "{")
            self.nextToken()

        elif self.checkToken(TokenType.ENDPROCEDURE) or self.checkToken(TokenType.ENDFUNCTION):
            self.nextToken()
            self.emitter.emitLine("\t}")
            self.emitter.isMethod = False

        elif self.checkToken(TokenType.RETURN):
            self.nextToken()
            self.emitter.emit("return ")
            self.primary()
            self.emitter.emitLine(";")

        elif self.checkToken(TokenType.CALL):
            self.nextToken()
            while not self.checkToken(TokenType.NEWLINE):
                self.emitter.emit(self.curToken.text)
                self.nextToken()

            self.emitter.emitLine(";")

        elif self.checkToken(TokenType.OUTPUT):
            self.nextToken()

            if self.checkToken(TokenType.STRING):
                self.emitter.emitLine(
                    f"Console.WriteLine(\"{self.curToken.text}\");")
                self.nextToken()
            else:
                # Not a simple string and there are expressions
                self.emitter.emit("Console.WriteLine($\"{")
                self.expression()
                if self.checkToken(TokenType.BRACKCLOSE):
                    self.emitter.emit(")")
                    self.match(TokenType.BRACKCLOSE)
                self.emitter.emitLine("}\");")

        # "IF" comparison "THEN" code "ENDIF"
        elif self.checkToken(TokenType.IF):
            self.nextToken()
            self.emitter.emit("if (")
            self.comparison()

            while not self.checkToken(TokenType.THEN):
                self.nextToken()

            self.match(TokenType.THEN)
            self.nl()
            self.emitter.emitLine(") {")

            while not self.checkToken(TokenType.ENDIF):
                self.statement()

            self.match(TokenType.ENDIF)
            self.emitter.emitLine("}")

        elif self.checkToken(TokenType.ELSE):
            self.nextToken()
            if self.checkToken(TokenType.IF):
                self.nextToken()
                self.emitter.emit("} else if (")
                self.comparison()

                while not self.checkToken(TokenType.THEN):
                    self.nextToken()

                self.match(TokenType.THEN)
                self.emitter.emitLine(") {")
            else:
                self.emitter.emitLine("} else {")

        elif self.checkToken(TokenType.CASE):
            self.nextToken()
            self.match(TokenType.OF)
            self.emitter.emitLine(f"switch ({self.curToken.text}) " + "{")
            self.match(TokenType.IDENT)
            self.nl()

            while not self.checkToken(TokenType.ENDCASE):
                if self.checkToken(TokenType.OTHERWISE):
                    self.emitter.emit("default")
                    self.nextToken()
                else:
                    self.emitter.emit("case ")
                    self.primary()
                    self.match(TokenType.COLON)

                self.emitter.emitLine(":")
                self.statement()

                self.emitter.emitLine("break;")

            self.emitter.emitLine("}")
            self.match(TokenType.ENDCASE)

        # "WHILE" comparison "REPEAT" code "ENDWHILE"
        elif self.checkToken(TokenType.WHILE):
            self.nextToken()
            self.emitter.emit("while (")
            self.comparison()

            self.match(TokenType.DO)
            self.nl()
            self.emitter.emitLine(") {")

            while not self.checkToken(TokenType.ENDWHILE):
                self.statement()

            self.match(TokenType.ENDWHILE)
            self.emitter.emitLine("}")

        elif self.checkToken(TokenType.REPEAT):
            self.nextToken()
            self.emitter.emitLine("do {")

            self.nl()
            while not self.checkToken(TokenType.UNTIL):
                self.statement()

            self.match(TokenType.UNTIL)
            self.emitter.emit("} while (!")
            self.comparison()
            self.emitter.emitLine(");")

        elif self.checkToken(TokenType.FOR):
            self.nextToken()
            ident = self.curToken.text
            self.emitter.emit(f"for (int {ident} = ")
            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)
            self.emitter.emit(f"{self.curToken.text};")
            self.match(TokenType.NUMBER)
            self.match(TokenType.TO)
            self.emitter.emitLine(
                f"{ident} < {self.curToken.text}; {ident}++) " + "{")
            self.match(TokenType.NUMBER)
            self.nl()

            while not self.checkToken(TokenType.ENDFOR) and not self.checkToken(TokenType.NEXT):
                self.statement()

            self.nextToken()
            if self.checkToken(TokenType.IDENT):
                self.nextToken()

            self.emitter.emitLine("}")

        # DECLARE ident: TYPE
        elif self.checkToken(TokenType.DECLARE):
            identString = ""
            while not self.checkToken(TokenType.COLON):
                self.nextToken()
                ident = self.curToken.text
                if ident in self.symbols:
                    self.abort(f"{ident} is already delcared")
                self.symbols.add(ident)
                self.match(TokenType.IDENT)
                identString += ident
                if self.checkToken(TokenType.COMMA):
                    identString += ','

            self.match(TokenType.COLON)
            self.emitter.emitLine(
                f"{self.typeConversion(self.curToken.text)} {identString};")
            self.match(TokenType.IDENT)

        elif self.checkToken(TokenType.IDENT):
            ident = self.curToken.text
            if ident.split('[')[0] not in self.symbols:
                self.abort(f"Identifier {self.curToken.text} not defined")
            self.nextToken()

            if self.checkToken(TokenType.BRACKOPEN):
                self.emitter.emit(ident)
                while not self.checkToken(TokenType.NEWLINE):
                    self.emitter.emit(self.curToken.text)
                    self.nextToken()
            elif self.checkToken(TokenType.EQ):
                self.match(TokenType.EQ)
                self.emitter.emit(f"{ident} = ")
                while not self.checkToken(TokenType.NEWLINE):
                    self.expression()

            self.emitter.emitLine(";")

        elif self.checkToken(TokenType.CONSTANT):
            self.nextToken()
            const = self.curToken.text
            if const in self.symbols:
                self.abort(f"Constant {self.curToken.text} is already defined")

            self.symbols.add(const)

            self.match(TokenType.IDENT)
            self.match(TokenType.EQEQ)
            dataType = self.typeConversion(self.curToken.kind.name)
            self.emitter.emit(f"const {dataType} {const} = ")
            self.expression()
            self.emitter.emitLine(";")

        # "INPUT" ident
        elif self.checkToken(TokenType.INPUT):
            self.nextToken()

            # If variable doesn't already exist, declare it.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.emitter.emitLine(f"string {self.curToken.text};")

            self.emitter.emitLine("Console.Write(\"Input: \");")
            self.emitter.emitLine(
                f"{self.curToken.text} = Console.ReadLine();")
            self.match(TokenType.IDENT)
        else:
            self.abort(
                f"Invalid statement at '{self.curToken.text}' ({self.curToken.kind.name})")

        # Must be a new line
        self.nl()

    def comparison(self):
        self.expression()
        while self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()

    def expression(self):
        self.term()
        # For + - expressions
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS) or self.checkToken(TokenType.BRACKOPEN):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.term()

    def term(self):
        self.unary()
        # for * / expressions
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.unary()

    def unary(self):
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS) or self.checkToken(TokenType.CONCAT):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        self.primary()

    def primary(self):
        if self.checkToken(TokenType.NUMBER) or self.checkToken(TokenType.TRUE) or self.checkToken(TokenType.FALSE) or self.checkToken(TokenType.BRACKCLOSE) or self.checkToken(TokenType.COMMA):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        elif self.checkToken(TokenType.STRING):
            self.emitter.emit(f"\"{self.curToken.text}\"")
            self.nextToken()
        elif self.checkToken(TokenType.CHAR):
            self.emitter.emit(f"'{self.curToken.text}'")
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            if self.curToken.text.split('[')[0] not in self.symbols and not self.checkPeek(TokenType.BRACKOPEN):
                self.abort(
                    f"Referencing variable before assignment: {self.curToken.text}")

            self.emitter.emit(self.curToken.text)
            self.nextToken()
        else:
            self.abort(
                f"Unexpected token at '{self.curToken.text}' ({self.curToken.kind.name})")

    def nl(self):
        self.match(TokenType.NEWLINE)
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

    def typeConversion(self, dataType):
        data = {"INTEGER": "int", "REAL": "float",
                "STRING": "string", "BOOLEAN": "bool", "CHAR": "char", "NUMBER": "float"}
        if dataType in data:
            return data[dataType]
        elif "ARRAY" in dataType:
            self.match(TokenType.ARRAY)
            self.match(TokenType.OF)
            return self.typeConversion(self.curToken.text) + "[]"
        else:
            self.abort(f"Undefined Type: ({dataType})")
