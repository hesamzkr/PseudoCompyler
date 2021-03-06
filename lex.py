import sys
import enum
# Lexer keeps track of current position in the source code and produces tokens to be parsed.


class Lexer:
    def __init__(self, input):
        self.source = input + '\n'
        self.curChar = ''
        self.curPos = -1
        self.nextChar()

    def nextChar(self):
        self.curPos += 1
        if self.curPos >= len(self.source):
            self.curChar = '\0'  # EOF
        else:
            self.curChar = self.source[self.curPos]

    def peek(self):
        if self.curPos + 1 >= len(self.source):
            return '\0'
        return self.source[self.curPos+1]

    def abort(self, message):
        txt = "{color}Lexing Error\n{message}{end}"
        sys.exit(txt.format(color="\033[91m", end="\033[0m", message=message))

    def getToken(self):
        self.skipWhitespace()
        self.skipComment()
        token = None

        if self.curChar == '&' and self.peek() == '&':
            token = Token('+', TokenType.CONCAT)
            self.nextChar()
        elif self.curChar == '(':
            token = Token(self.curChar, TokenType.BRACKOPEN)
        elif self.curChar == ')':
            token = Token(self.curChar, TokenType.BRACKCLOSE)
        elif self.curChar == ',':
            token = Token(self.curChar, TokenType.COMMA)
        elif self.curChar == '+':
            token = Token(self.curChar, TokenType.PLUS)
        elif self.curChar == '-':
            token = Token(self.curChar, TokenType.MINUS)
        elif self.curChar == '*':
            token = Token(self.curChar, TokenType.ASTERISK)
        elif self.curChar == '/':
            token = Token(self.curChar, TokenType.SLASH)
        elif self.curChar == '=':
            token = Token("==", TokenType.EQEQ)
        elif self.curChar == '>':
            # Check whether it's token is > or >=
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.GTEQ)
            else:
                token = Token(self.curChar, TokenType.GT)
        elif self.curChar == '<':
            # Check whether it's token is <- or <> or <= or <
            if self.peek() == '-':
                self.nextChar()
                token = Token("=", TokenType.EQ)
            elif self.peek() == '>':
                self.nextChar()
                token = Token("!=", TokenType.NOTEQ)
            elif self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.LTEQ)
            else:
                token = Token(self.curChar, TokenType.LT)
        elif self.curChar == '!':
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.NOTEQ)
            else:
                self.abort("Expected !=, got !" + self.peek())

        elif self.curChar == ':':
            token = Token(':', TokenType.COLON)
        elif self.curChar == '\"':
            self.nextChar()
            startPos = self.curPos

            while self.curChar != '\"':
                self.nextChar()

            tokText = self.source[startPos: self.curPos]
            token = Token(tokText, TokenType.STRING)
        elif self.curChar == "'":
            self.nextChar()
            token = Token(self.curChar, TokenType.CHAR)
            self.nextChar()
            if self.curChar != "'":
                self.abort(f"Invalid character at '{token.text}'")

        elif self.curChar.isdigit():
            startPos = self.curPos
            while self.peek().isdigit():
                self.nextChar()
            if self.peek() == '.':
                self.nextChar()

                if not self.peek().isdigit():
                    self.abort("Illegal character in number.")
                while self.peek().isdigit():
                    self.nextChar()

            tokText = self.source[startPos: self.curPos + 1]
            token = Token(tokText, TokenType.NUMBER)
        elif self.curChar.isalpha():
            startPos = self.curPos
            while self.peek().isalnum():
                self.nextChar()

            tokText = self.source[startPos: self.curPos + 1]
            keyword = Token.checkIfKeyword(tokText)
            if keyword == None:
                if self.peek() == '[':
                    self.nextChar()
                    tokText = self.source[startPos: self.curPos + 1]
                    tempPos = self.curPos + 1
                    while self.curChar != ']':
                        self.nextChar()
                    tokText += f"{self.source[tempPos: self.curPos]} - 1]"
                    token = Token(tokText, TokenType.IDENT)
                else:
                    token = Token(tokText, TokenType.IDENT)
            else:
                if keyword == TokenType.FALSE:
                    tokText = "false"
                elif keyword == TokenType.TRUE:
                    tokText = "true"
                elif keyword == TokenType.AND:
                    tokText = "&&"
                elif keyword == TokenType.OR:
                    tokText = "||"
                elif keyword == TokenType.NOT:
                    tokText = "!"
                elif keyword == TokenType.ARRAY:
                    while not self.curChar == ']':
                        self.nextChar()
                    tokText = self.source[startPos: self.curPos + 1]
                token = Token(tokText, keyword)
        elif self.curChar == '\n':
            token = Token('\n', TokenType.NEWLINE)
        elif self.curChar == '\0':
            # End Of File
            token = Token('', TokenType.EOF)
        else:
            self.abort(f"Unknown token: {self.curChar}")

        self.nextChar()
        return token

    # Skip whitespace except newlines, since they're used to indicate the end of a statement.
    def skipWhitespace(self):
        while self.curChar == ' ' or self.curChar == '\t' or self.curChar == '\r':
            self.nextChar()

    def skipComment(self):
        if self.curChar == '/' and self.peek() == '/':
            while self.curChar != '\n':
                self.nextChar()


class Token:
    def __init__(self, tokenText, tokenKind):
        self.text = tokenText
        self.kind = tokenKind

    def __str__(self):
        return f"kind: {self.kind}, text: {self.text}"

    @staticmethod
    def checkIfKeyword(tokenText):
        for kind in TokenType:
            # Keyword enum values between 100 and 200
            if kind.name == tokenText and kind.value >= 100 and kind.value < 200:
                return kind
        return None


class TokenType(enum.Enum):
    EOF = -1
    NEWLINE = 0
    NUMBER = 1
    IDENT = 2
    STRING = 3
    INDEX = 4
    BRACKOPEN = 5
    BRACKCLOSE = 6
    CHAR = 7
    # Keywords.
    OUTPUT = 103
    INPUT = 104
    DECLARE = 105
    IF = 106
    THEN = 107
    ELSE = 108
    ENDIF = 109
    WHILE = 110
    REPEAT = 111
    ENDWHILE = 112
    AND = 113
    OR = 114
    DO = 115
    FOR = 116
    TO = 117
    ENDFOR = 118
    NEXT = 119
    UNTIL = 120
    CASE = 121
    OF = 122
    OTHERWISE = 123
    ENDCASE = 124
    NOT = 125
    CONSTANT = 126
    PROCEDURE = 127
    ENDPROCEDURE = 128
    FUNCTION = 129
    ENDFUNCTION = 130
    RETURNS = 131
    RETURN = 132
    CALL = 133
    FALSE = 134
    TRUE = 135
    ARRAY = 136
    # Operators.
    EQ = 201
    PLUS = 202
    MINUS = 203
    ASTERISK = 204
    SLASH = 205
    EQEQ = 206
    NOTEQ = 207
    LT = 208
    LTEQ = 209
    GT = 210
    GTEQ = 211
    CONCAT = 212
    COLON = 213
    COMMA = 214
