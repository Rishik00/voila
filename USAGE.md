# Using voila

`voila` is a small grammar-first DSL for elementwise vector addition and
multiplication. It uses NumPy for execution.

## 1. Install the dependency

```bash
python -m pip install numpy
```

## 2. Build an expression with Python operators

```python
import numpy as np
from voila import Vector, evaluate

x = Vector("x", 4)
y = Vector("y", 4)
expression = (x + y) * 2

result = evaluate(expression, {
    "x": np.array([1, 2, 3, 4]),
    "y": np.array([5, 6, 7, 8]),
})
print(result)  # [12 16 20 24]
```

Vector lengths are checked when the expression is created and input lengths
are checked when it is evaluated. Scalars can be mixed into expressions.

## 3. Parse the expression grammar

The parser accepts vector names, numeric constants, parentheses, unary minus,
`+`, and `*`:

```python
from voila import parse

expression = parse("-x + (y * 3)", {"x": 4, "y": 4})
```

The parser returns the same AST type produced by Python operators.

## 4. Compile a reusable NumPy callable

```python
run = expression.compile()
result = run([1, 2, 3, 4], [1, 1, 1, 1])
print(result)  # [2 1 0 -1]
```

Inputs are passed positionally in alphabetical name order, or by keyword:

```python
run(x=[1, 2, 3, 4], y=[1, 1, 1, 1])
```

Run the complete example with:

```bash
python run.py
```
