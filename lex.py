import sys
import enum

# Lexer object keeps track of current position in the source code and produces each token.


class Lexer:
    def __init__(self, input):
        # Source code to lex as a string. Append a newline to simplify lexing/parsing the last token/statement.
        self.source = input + '\n'
        self.curChar = ''   # Current character in the string.
        self.curPos = -1    # Current position in the string.
        self.nextChar()

    # Process the next character.
    def nextChar(self):
        self.curPos += 1
        if self.curPos >= len(self.source):
            self.curChar = '\0'  # EOF
        else:
            self.curChar = self.source[self.curPos]

    # Return the lookahead character.
    def peek(self):
        if self.curPos + 1 >= len(self.source):
            return '\0'
        return self.source[self.curPos+1]

    # Invalid token found, print error message and exit.
    def abort(self, message):
        txt = "{color}Lexing Error\n{message}{end}"
        sys.exit(txt.format(color="\033[91m", end="\033[0m", message=message))

    # Return the next token.
    def getToken(self):
        self.skipWhitespace()
        self.skipComment()
        token = None

        # Check the first character of this token to see if we can decide what it is.
        # If it is a multiple character operator (e.g., !=), number, identifier, or keyword, then we will process the rest.
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
            # Check whether this is token is > or >=
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.GTEQ)
            else:
                token = Token(self.curChar, TokenType.GT)
        elif self.curChar == '<':
            # Check whether this is token is <- or <= or <
            if self.peek() == '-':
                self.nextChar()
                # startPos = self.curPos + 1
                # while self.peek() != '\n':
                #     self.nextChar()
                # text = self.source[startPos: self.curPos + 1]
                # token = Token(text.strip(), TokenType.EQ)
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
            # Get characters between quotations.
            self.nextChar()
            startPos = self.curPos

            while self.curChar != '\"':
                self.nextChar()
                # Don't allow special characters in the string. No escape characters, newlines, tabs, or %.
                # We will be using C's printf on this string.
                # if self.curChar == '\r' or self.curChar == '\n' or self.curChar == '\t' or self.curChar == '\\':
                # self.abort("Illegal character in string.")

            tokText = self.source[startPos: self.curPos]  # Get the substring.
            token = Token(tokText, TokenType.STRING)
        elif self.curChar == "'":
            self.nextChar()
            token = Token(self.curChar, TokenType.CHAR)
            self.nextChar()
            if self.curChar != "'":
                self.abort(f"Invalid character at '{token.text}'")

        elif self.curChar.isdigit():
            # Leading character is a digit, so this must be a number.
            # Get all consecutive digits and decimal if there is one.
            startPos = self.curPos
            while self.peek().isdigit():
                self.nextChar()
            if self.peek() == '.':  # Decimal!
                self.nextChar()

                # Must have at least one digit after decimal.
                if not self.peek().isdigit():
                    # Error!
                    self.abort("Illegal character in number.")
                while self.peek().isdigit():
                    self.nextChar()

            # Get the substring.
            tokText = self.source[startPos: self.curPos + 1]
            token = Token(tokText, TokenType.NUMBER)
        elif self.curChar.isalpha():
            # Leading character is a letter, so this must be an identifier or a keyword.
            # Get all consecutive alpha numeric characters.
            startPos = self.curPos
            while self.peek().isalnum():
                self.nextChar()

            # Check if the token is in the list of keywords.
            # Get the substring.
            tokText = self.source[startPos: self.curPos + 1]
            keyword = Token.checkIfKeyword(tokText)
            if keyword == None:
                if self.peek() == '[':
                    while self.curChar != ']':
                        self.nextChar()
                    tokText = self.source[startPos: self.curPos + 1]
                    token = Token(tokText, TokenType.INDEX)
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
                token = Token(tokText, keyword)
        elif self.curChar == '\n':
            # Newline.
            token = Token('\n', TokenType.NEWLINE)
        elif self.curChar == '\0':
            # EOF.
            token = Token('', TokenType.EOF)
        else:
            # Unknown token!
            self.abort("Unknown token: " + self.curChar)

        self.nextChar()
        return token

    # Skip whitespace except newlines, which we will use to indicate the end of a statement.
    def skipWhitespace(self):
        while self.curChar == ' ' or self.curChar == '\t' or self.curChar == '\r':
            self.nextChar()

    def skipComment(self):
        if self.curChar == '/' and self.peek() == '/':
            while self.curChar != '\n':
                self.nextChar()


# Token contains the original text and the type of token.
class Token:
    def __init__(self, tokenText, tokenKind):
        # The token's actual text. Used for identifiers, strings, and numbers.
        self.text = tokenText
        # The TokenType that this token is classified as.
        self.kind = tokenKind

    def __str__(self):
        return f"kind: {self.kind}, text: {self.text}"

    @staticmethod
    def checkIfKeyword(tokenText):
        for kind in TokenType:
            # Relies on all keyword enum values being 1XX.
            if kind.name == tokenText and kind.value >= 100 and kind.value < 200:
                return kind
        return None


# TokenType is our enum for all the types of tokens.
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
    LABEL = 101
    GOTO = 102
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
