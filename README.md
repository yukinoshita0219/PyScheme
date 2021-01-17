# PyScheme
A Scheme Interpreter Implemented in Python with Starter Code from the [CS 61A](https://cs61a.org/) [Scheme Challenge Version Project](https://cs61a.org/proj/scheme_stubbed/).

_Only covers features within the [project](https://cs61a.org/proj/scheme_stubbed/) (including optional ones)._

## Usage
In a Terminal, set the current directory to be the folder ```scheme_stubbed```, and then type:
```
python3 scheme
```
The Scheme prompt will show as:
```
scm> 
```
To exit the Scheme interpreter, press ```Ctrl-D``` or evaluate the ```exit``` procedure:
```
scm> (exit)
```
### Examples
```
scm> +
#[+]
scm> odd?
#[odd?]
scm> display
#[display]

scm> (+ 1 2)
3
scm> (* 3 4 (- 5 2) 1)
36
scm> (odd? 31)
#t

scm> (define x 15)
x
scm> x
15
scm> (eval 'x)
15
scm> (define y (* 2 x))
y
scm> y
30
scm> (+ y (* y 2) 1)
91
scm> (define x 20)
x
scm> x
20

scm> (quote a)
a
scm> (quote (1 2))
(1 2)
scm> (quote (1 (2 three (4 5))))
(1 (2 three (4 5)))
scm> 'hello
hello
scm> (eval (cons 'car '('(1 2))))
1
```
## Reference
[CS 61A](https://cs61a.org/)

[Scheme Challenge Version](https://cs61a.org/proj/scheme_stubbed/)
