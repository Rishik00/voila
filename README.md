# voila

Voila is a simple sympy to triton/numpy compiler. It's relying a lot on the ast module to convert from source (sympy's expression trees) to target (numpy/triton kernels). 

# Usage 

````python
from voila import csymbol, eval_expression

a = csymbol('a', shape=(1, 5), dtype="float16")
b = csymbol('b', shape=(1, 5), dtype="float16")
c = csymbol('c', shape=(1, 5), dtype="float16")
d = csymbol('d', shape=(1, 5), dtype="float16")

expr1 = a + b + c
expr2 = b + d

print(eval_expression(expr1))
print(eval_expression(expr2))
````

# TODO next

- [ ] Support scalar multiplication
- [ ] Support matrix multiplication
- [ ] Handle nested expressions correctly, e.g. `a + b * c`
- [ ] Generalize AST lowering beyond direct `ConvSymbol(...)` arguments
- [ ] Optimize n-ary addition lowering
- [ ] Add shape validation and basic shape inference
- [ ] Add dtype propagation / validation
- [ ] Implement lazy realization
  - Parse and lower the full expression first
  - Discover dependencies using `expr.free_symbols`
  - Realize only the symbols required by the expression
  - Dynamically construct the evaluation namespace
- [ ] Separate parsing/lowering from execution