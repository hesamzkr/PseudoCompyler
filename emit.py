# Emitter generates the code for different sections and outputs it.
class Emitter:
    def __init__(self, fullPath):
        self.fullPath = fullPath
        self.header = ""
        self.main = ""
        self.methodCode = ""
        self.isMethod = False

    def emit(self, code):
        if (self.isMethod):
            self.methodCode += code
        else:
            self.main += code

    def emitLine(self, code):
        self.emit(code + '\n')

    def headerLine(self, code):
        self.header += code + '\n'

    def writeFile(self):
        with open(self.fullPath, 'w+') as outputFile:
            outputFile.write(self.header + self.main +
                             self.methodCode + "\n}")
