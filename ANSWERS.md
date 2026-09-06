# Answers to the implementation questions

The complete review transcript, with every original question preserved verbatim,
is in [QUESTIONS.md](QUESTIONS.md). This file gives the shorter design summary;
`QUESTIONS.md` is the authoritative one-question/one-answer walkthrough.

## Why is `Expression` a dataclass?

`Expression` is a small immutable AST node. `@dataclass(frozen=True)` supplies
structural storage, a useful representation, and safe value semantics without
boilerplate. It is still created through vector operators or `parse()` in
normal use; direct construction remains available for AST inspection and
experimentation.

## How can an expression be created?

There are two supported paths:

```python
from voila import Vector, parse

x = Vector("x", 4)
y = Vector("y", 4)
by_operator = (x + y) * 2
by_parser = parse("(x + y) * 2", {"x": 4, "y": 4})
```

The operator path builds the project AST directly. The parser path first uses
Python's syntax tree as a safe front end, then `Grammar` converts supported
nodes into the same project AST. The `vector` name is retained as a backwards-
compatible alias for `Vector`.

## Why is `Expression` public, and why is `Grammar` public?

Both are useful while this is a proof of concept: callers can inspect the AST
and extend or test the grammar. `ast.NodeVisitor` is only the parser mechanism;
`Expression` and `Vector` are the domain AST. Each `visit_*` method is called by
`visit()` based on the Python AST node's class, so `visit_BinOp` handles `+` and
`*`, while `visit_Name` handles vector names.

## Why does `x * 2` not call `visit_UnaryOp`?

`x * 2` is a binary operation, so Python produces `ast.BinOp` and the parser
calls `visit_BinOp`. `visit_UnaryOp` is only for one-operand operators such as
`-x`. The parser accepts `ast.USub` because unary minus is the only unary
operation in the MVP; other unary operations are rejected deliberately.

## Are we making our own AST?

Yes. Python's `ast` tree is an input grammar tree, not the project's runtime
representation. `Grammar` lowers the supported Python nodes into `Vector` and
`Expression`, which are the AST consumed by `evaluate()` and `compile()`.

## What do the recursive helpers do?

`_inputs()` returns the unique vector names needed by an expression, so compiled
callables know their argument order. `_walk()` visits every AST leaf, which lets
`evaluate()` validate each vector's declared length. They look similar because
both traverse the tree, but they answer different questions and intentionally
stay small for the MVP.

## Does every vector need `.compile()`?

No. The module-level `compile(expr)` is sufficient. `.compile()` on `Vector` and
`Expression` is a convenience so either a leaf or a composed expression can be
run consistently; it delegates to that one implementation.
