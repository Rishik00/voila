# voila

A small grammar-first symbolic DSL for writing vector math.

Define variables with tensor metadata, compose equations with normal Python operators,
and call `.compile()` to create a fast NumPy-backed callable.

---

## MVP: vector add and multiply

The first usable slice is available in `voila.py`:

```python
from voila import Vector, evaluate, parse

x = Vector("x", 4)
y = Vector("y", 4)
expr = (x + y) * 2

assert evaluate(expr, {"x": [1, 2, 3, 4], "y": [5, 6, 7, 8]}).tolist() == [12, 16, 20, 24]
print(evaluate(expr, {"x": [1, 2, 3, 4], "y": [5, 6, 7, 8]}))
```

Expressions can also be written with the MVP grammar and parsed into the same
AST:

```python
expr = parse("(x + y) * 2", {"x": 4, "y": 4})
run = expr.compile()
print(run([1, 2, 3, 4], [5, 6, 7, 8]))
```

The grammar supports names, numeric constants, parentheses, unary minus, `+`,
and `*`. NumPy handles the elementwise execution, while the AST validates
vector sizes and input shapes before evaluating.

## Core idea

The gap this fills: you think about a computation as math (`σ(Wx + b)`), but to implement
it fast you have to write low-level array code — an entirely different mental model. This library
lets you stay in math space and generate the kernel.

Because the representation is symbolic, the expression can be inspected and
compiled separately from execution. Backend code generation is intentionally
outside the MVP.

---


## DAG

A series of equations forms a DAG. The DAG representation enables:

1. **Fusion boundaries** — reductions are synchronization points. Everything between
   two reductions can be fused into one kernel pass. Without an explicit DAG you can't
   reason about where to split.

2. **CSE** — if `x + y` appears in two branches, the DAG sees it's the same node and
   computes it once instead of emitting two kernels.

3. **Automatic gradients** — the forward DAG is the computation. The reverse DAG is
   backprop. Since every node is symbolic, `.diff()` on each node wires up the backward
   graph automatically.

`dag.compile()` returns one kernel per fusion group, where group boundaries are
reduction nodes.

---
