# Compiler for Cambridge A Level Pseudoscience

Run with:
`python main.py <path/to/file.txt>`

eg.
`python main.py pseudo.txt`


Example:

```cpp
FUNCTION Calculate(op: CHAR) RETURNS REAL
   DECLARE x : INTEGER
   DECLARE y : INTEGER
   DECLARE ans : REAL
   x <- 1
   y <- 2

   CASE OF op
       '+' : ans <- x + y
       '-' : ans <- x - y
       '*' : ans <- x * y
       '/' : ans <- x / y
       OTHERWISE OUTPUT "ERROR"
   ENDCASE

   IF operator <> '+' AND operator <> '-' AND operator <> '*' AND operator <> '/'
       THEN
           RETURN -1
       ELSE
           RETURN ans
   ENDIF
ENDFUNCTION

DECLARE operator : CHAR

OUTPUT Calculate(operator)
```
