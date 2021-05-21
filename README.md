# Compiler for Cambridge IA Level CS PseudoCode
## Prerequisites
The C# compiler is required to be able to run this, as the pseudocode is first translated to C# before using Roslyn to compile it into an executable.
It can be downloaded [here](https://github.com/dotnet/roslyn) or by downloading [Visual Studio](https://visualstudio.microsoft.com/vs/community/).
<br/>


## How To Use
Run with:
`python main.py <path/to/file.txt>`

eg.
`python main.py pseudo.txt`
<br/>


## Pseudocode Example
```cpp
FUNCTION Calculate(op: CHAR) RETURNS REAL
   DECLARE x : INTEGER
   DECLARE y : INTEGER
   DECLARE ans : REAL
   ans <- 0
   x <- 1
   y <- 2

   CASE OF op
       '+' : ans <- x + y
       '-' : ans <- x - y
       '*' : ans <- x * y
       '/' : ans <- x / y
       OTHERWISE OUTPUT "ERROR"
   ENDCASE

   IF op <> '+' AND op <> '-' AND op <> '*' AND op <> '/'
       THEN
           RETURN 0
       ELSE
           RETURN ans
   ENDIF
ENDFUNCTION

DECLARE test : CHAR
test <- '+'
OUTPUT Calculate(test)
```
