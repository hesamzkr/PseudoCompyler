import sys
import re
from lex import *

# Parser object keeps track of current token, checks if the code matches the grammar, and emits code along the way.


class Parser:
    def __init__(self, lexer, emitter):
        self.lexer = lexer
        self.emitter = emitter

        self.symbols = set()    # All variables we have declared so far.
        self.labelsDeclared = set()  # Keep track of all labels declared
        # All labels goto'ed, so we know if they exist or not.
        self.labelsGotoed = set()

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken()    # Call this twice to initialize current and peek.

    # Return true if the current token matches.
    def checkToken(self, kind):
        return kind == self.curToken.kind

    # Return true if the next token matches.
    def checkPeek(self, kind):
        return kind == self.peekToken.kind

    # Try to match current token. If not, error. Advances the current token.
    def match(self, kind):
        if not self.checkToken(kind):
            self.abort(
                f"Expected ({kind.name}), got ({self.curToken.kind.name}), text: {self.curToken.text}")
        self.nextToken()

    # Advances the current token.
    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()
        # No need to worry about passing the EOF, lexer handles that.

    # Return true if the current token is a comparison operator.
    def isComparisonOperator(self):
        return self.checkToken(TokenType.GT) or self.checkToken(TokenType.GTEQ) or self.checkToken(TokenType.LT) or self.checkToken(TokenType.LTEQ) or self.checkToken(TokenType.EQEQ) or self.checkToken(TokenType.NOTEQ) or self.checkToken(TokenType.AND) or self.checkToken(TokenType.OR) or self.checkToken(TokenType.NOT)

    def abort(self, message):
        txt = "{color}Parse Error\n{message}{end}"
        sys.exit(txt.format(color="\033[91m", end="\033[0m", message=message))

    # Production rules.

    # program ::= {statement}

    def program(self):
        self.emitter.headerLine(
            "using System;\nusing System.IO;\nusing System.Linq;\nusing System.Collections.Generic;\n")
        self.emitter.headerLine(
            "class Program\n{\n\tpublic static void Main(string[] args)\n\t{")

        # Since some newlines are required in our grammar, need to skip the excess.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

        # Parse all the statements in the program.
        while not self.checkToken(TokenType.EOF):
            self.statement()

        # Wrap things up.
        self.emitter.emitLine("\t}")

        # Check that each label referenced in a GOTO is declared.
        # for label in self.labelsGotoed:
        #     if label not in self.labelsDeclared:
        #         self.abort("Attempting to GOTO to undeclared label: " + label)

    # One of the following statements...

    def statement(self):
        # Check the first token to see what kind of statement this is.

        # "OUTPUT" (expression | string)
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

            # public static int Max(int Number1, int Number2) {
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
                # Simple string, so print it.
                self.emitter.emitLine(
                    f"Console.WriteLine(\"{self.curToken.text}\");")
                self.nextToken()
            else:
                # Expect an expression and print the result as a float.
                self.emitter.emit("Console.WriteLine($\"{")
                self.expression()
                self.emitter.emitLine("}\");")

        # "IF" comparison "THEN" block "ENDIF"
        elif self.checkToken(TokenType.IF):
            self.nextToken()
            self.emitter.emit("if (")
            self.comparison()

            while not self.checkToken(TokenType.THEN):
                self.nextToken()

            self.match(TokenType.THEN)
            self.nl()
            self.emitter.emitLine(") {")

            # Zero or more statements in the body.
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

        # "WHILE" comparison "REPEAT" block "ENDWHILE"
        elif self.checkToken(TokenType.WHILE):
            self.nextToken()
            self.emitter.emit("while (")
            self.comparison()

            self.match(TokenType.DO)
            self.nl()
            self.emitter.emitLine(") {")

            # Zero or more statements in the loop body.
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

        # "DECLARE" ident = expression
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
            if ident not in self.symbols:
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

        elif self.checkToken(TokenType.INDEX):
            ident = self.curToken.text
            if ident.split('[')[0] not in self.symbols:
                self.abort(f"Identifier {self.curToken.text} not defined")
            self.nextToken()
            self.emitter.emitLine(f"{ident} = {self.curToken.text};")
            self.nextToken()

        # "INPUT" ident
        elif self.checkToken(TokenType.INPUT):
            self.nextToken()

            # If variable doesn't already exist, declare it.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.emitter.emitLine(f"string {self.curToken.text};")

            # Emit scanf but also validate the input. If invalid, set the variable to 0 and clear the input.
            self.emitter.emitLine("Console.Write(\"Input: \");")
            self.emitter.emitLine(
                f"{self.curToken.text} = Console.ReadLine();")
            self.match(TokenType.IDENT)
        # This is not a valid statement. Error!
        else:
            self.abort(
                f"Invalid statement at '{self.curToken.text}' ({self.curToken.kind.name})")
        # Newline.
        self.nl()

    # comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+

    def comparison(self):
        self.expression()
        while self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()

    # expression ::= term {( "-" | "+" ) term}

    def expression(self):
        self.term()
        # Can have 0 or more +/- and expressions.
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS) or self.checkToken(TokenType.BRACKOPEN):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.term()

    # term ::= unary {( "/" | "*" ) unary}

    def term(self):
        self.unary()
        # Can have 0 or more *// and expressions.
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.unary()

    # unary ::= ["+" | "-"] primary

    def unary(self):
        # Optional unary +/-
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS) or self.checkToken(TokenType.CONCAT):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        self.primary()

    # primary ::= number | ident

    def primary(self):
        if self.checkToken(TokenType.NUMBER) or self.checkToken(TokenType.INDEX) or self.checkToken(TokenType.TRUE) or self.checkToken(TokenType.FALSE) or self.checkToken(TokenType.BRACKCLOSE):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        elif self.checkToken(TokenType.STRING):
            self.emitter.emit(f"\"{self.curToken.text}\"")
            self.nextToken()
        elif self.checkToken(TokenType.CHAR):
            self.emitter.emit(f"'{self.curToken.text}'")
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            # Ensure the variable already exists.
            if self.curToken.text not in self.symbols and not self.checkPeek(TokenType.BRACKOPEN):
                self.abort(
                    f"Referencing variable before assignment: {self.curToken.text}")

            self.emitter.emit(self.curToken.text)
            self.nextToken()
        else:
            # Error!
            self.abort(
                f"Unexpected token at '{self.curToken.text}' ({self.curToken.kind.name})")

    # nl ::= '\n'+
    def nl(self):
        # Require at least one newline.
        self.match(TokenType.NEWLINE)
        # But we will allow extra newlines too, of course.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

    def typeConversion(self, dataType):
        data = {"INTEGER": "int", "REAL": "float",
                "STRING": "string", "BOOLEAN": "bool", "CHAR": "char", "NUMBER": "float"}
        if dataType in data:
            return data[dataType]
        elif "ARRAY" in dataType:
            self.match(TokenType.INDEX)
            self.match(TokenType.OF)
            return self.typeConversion(self.curToken.text) + "[]"
        else:
            self.abort(f"Undefined Type: ({dataType})")
