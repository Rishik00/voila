"""Small grammar-first vector expression MVP.

The public surface is intentionally small: parse an expression, inspect its
AST, evaluate it with NumPy, or compile it into a reusable NumPy function.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from numbers import Number
from typing import Mapping

import numpy as np

# Review: can go to utils.py
class ShapeError(ValueError):
    """Raised when vectors in an expression do not have compatible shapes."""

# Review: can go to utils.py
def _operand_ok(value):
    return isinstance(value, (Vector, Expression)) or (
        isinstance(value, Number) and not isinstance(value, bool)
    )

# Question: why is this a dataclass?
# Answer: a frozen dataclass provides named fields, structural equality, a
# useful repr, and immutability without boilerplate.

# Question: here's another problem, what are the pathways for me to make an expression? 
# Answer: use Vector operators such as `(x + y) * 2`, or parse equivalent source
# with `parse("(x + y) * 2", {"x": 4, "y": 4})`.

# The way I see it, there's nothing stopping anyone from just making an expression via this class directly.
# Answer: correct; direct construction is possible for AST experimentation.
# Normal callers should use operators or parse(), which validate the pathway.
    
# Not sure if that makes full sense here. I think that the expressions class should only be visible via vectors. 
# Answer: that narrower API is reasonable, but Expression stays public in this
# PoC so callers can inspect and extend the AST.

# Question: and why is this public? 
# Answer: Expression is public for AST inspection; underscore-prefixed helpers
# are private because they are implementation details.
@dataclass(frozen=True)
class Expression:
    """An immutable AST node for one vector operation."""

    op: str
    left: "Vector | Expression | Number"
    right: "Vector | Expression | Number"

    @property
    def size(self):
        sizes = [item.size for item in (self.left, self.right) if hasattr(item, "size")]
        if not sizes:
            return None
        if any(size != sizes[0] for size in sizes[1:]):
            raise ShapeError(f"vector sizes do not match: {sizes[0]} and {sizes[1]}")
        return sizes[0]

    def __add__(self, other):
        if not _operand_ok(other):
            return NotImplemented
        return Expression("add", self, other)

    def __radd__(self, other):
        if not _operand_ok(other):
            return NotImplemented
        return Expression("add", other, self)

    def __mul__(self, other):
        if not _operand_ok(other):
            return NotImplemented
        return Expression("mul", self, other)

    def __rmul__(self, other):
        if not _operand_ok(other):
            return NotImplemented
        return Expression("mul", other, self)

    def __neg__(self):
        return Expression("mul", -1, self)

    def compile(self):
        return compile(self)

    def __repr__(self):
        return f"({self.left!r} {self.op} {self.right!r})"


class Vector:
    """A named one-dimensional vector with a fixed length."""

    def __init__(self, name: str, size: int):
        if not isinstance(name, str) or not name.isidentifier():
            raise ValueError("name must be a valid Python identifier")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise ValueError("size must be a positive integer")
        self.name = name
        self.size = size

    def __add__(self, other):
        if not _operand_ok(other):
            return NotImplemented
        return Expression("add", self, other)

    def __radd__(self, other):
        if not _operand_ok(other):
            return NotImplemented
        return Expression("add", other, self)

    def __mul__(self, other):
        if not _operand_ok(other):
            return NotImplemented
        return Expression("mul", self, other)

    def __rmul__(self, other):
        if not _operand_ok(other):
            return NotImplemented
        return Expression("mul", other, self)

    def __neg__(self):
        return Expression("mul", -1, self)

    # Question: does every vector need a compile function? 
    # Answer: no. The module-level compile(expr) is sufficient; this method is a
    # convenience so a Vector and an Expression share one API.
    def compile(self):
        return compile(self)

    def __repr__(self):
        return f"Vector({self.name!r}, size={self.size})"

# Review: don't do this. Lets expose the Vector directly for this PoC. 
# Answer: Vector is the primary public class; vector() remains only as a
# compatibility convenience. The direct PoC API is `Vector("x", 4)`.
def vector(name: str, size: int) -> Vector:
    return Vector(name, size)

# Question: why is this private? 
# Answer: callers only need parse(), but Grammar is public in this PoC so it can
# be inspected and extended.

# Question: alright I was inspecting this, and found it rather...bizzare
# Answer: Python's syntax tree is the parser input; Grammar lowers it into our
# Vector/Expression runtime AST, keeping unsupported syntax out of evaluation.

# Question: how does this ast.NodeVisitor work? And how are you registeri
# Answer: visit(node) dispatches by node class name: ast.BinOp calls visit_BinOp,
# ast.Name calls visit_Name, and so on. No manual registration is needed.
class Grammar(ast.NodeVisitor):
    """Parser for: expression := term ((+ | *) term)*, with parentheses."""

    def __init__(self, sizes: Mapping[str, int]):
        self.sizes = sizes

    # Question: wait, are these even being called?
    # Answer: yes. parse() calls Grammar.visit() on the root, which recursively
    # dispatches to the visit_* methods. run.py exercises this path.
    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Name(self, node):
        if node.id not in self.sizes:
            raise ValueError(f"unknown vector {node.id!r}")
        return vector(node.id, self.sizes[node.id])

    def visit_Constant(self, node):
        if isinstance(node.value, bool) or not isinstance(node.value, Number):
            raise ValueError("only numeric scalar constants are supported")

        return node.value

    def visit_BinOp(self, node):
        left, right = self.visit(node.left), self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Mult):
            return left * right
        raise ValueError("grammar only supports + and *")

    # Question: when I do x * 2, why are we not triggering visit_UnaryOp
    # Answer: x * 2 has two operands, so Python represents it as ast.BinOp.
    # visit_UnaryOp is only for one-operand expressions such as -x.
    def visit_UnaryOp(self, node):
        # Question: why are we only checking for ast.USu
        # Question: why are we only checking for ast.USub
        # Answer: USub is unary minus, the only unary operation supported by this MVP.
        if isinstance(node.op, ast.USub):
            value = self.visit(node.operand)
            return -value if isinstance(value, (Vector, Expression)) else -value
        raise ValueError("grammar only supports unary minus")

    def generic_visit(self, node):
        # Question: Why do i need a generic visit
        # Answer: this is the rejection path for syntax not supported by the MVP.
        raise ValueError(f"unsupported syntax: {type(node).__name__}")

# Question: hmm, so we're not making our own AST?
# Answer: we are. Python's ast tree is parser input; Grammar lowers it into our
# Vector/Expression AST, which evaluate() and compile() consume.
def parse(source: str, sizes: Mapping[str, int]):
    """Parse ``+``/``*`` vector grammar into a symbolic AST."""

    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty expression")
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"invalid expression: {exc.msg}") from exc
    return Grammar(sizes).visit(tree)

# Review: can go to utils.py
def _inputs(expr):
    if isinstance(expr, Vector):
        return {expr.name}
    if isinstance(expr, Number):
        return set()

    # Question: what is this doing even? 

    # Answer: it recursively visits both branches and unions their names, producing
    # the unique input set used to order compiled callable arguments.
    return _inputs(expr.left) | _inputs(expr.right)

# Review: can go to utils.py
def _numpy_value(expr, values):
    if isinstance(expr, Vector):
        return values[expr.name]
    if isinstance(expr, Number):
        return expr
    left, right = _numpy_value(expr.left, values), _numpy_value(expr.right, values)
    return np.add(left, right) if expr.op == "add" else np.multiply(left, right)


def evaluate(
        expr, 
        values: Mapping[str, object]
    ):
    """Evaluate an AST with NumPy, returning a one-dimensional ndarray."""

    if not isinstance(expr, (Vector, Expression)):
        raise TypeError("expr must be a Vector or Expression")
    arrays = {}
    for name in _inputs(expr):
        if name not in values:
            raise KeyError(f"missing values for vector {name!r}")
        array = np.asarray(values[name])
        if array.ndim != 1:
            raise ShapeError(f"{name!r} must be one-dimensional")

        expected = next(item.size for item in _walk(expr) if isinstance(item, Vector) and item.name == name)
        if len(array) != expected:
            raise ShapeError(f"{name!r} has length {len(array)}, expected {expected}")

        arrays[name] = array
    return np.asarray(_numpy_value(expr, arrays))

# Review: can go to utils.py
def _walk(expr):
    if isinstance(expr, (Vector, Number)):
        yield expr
    else:
        yield from _walk(expr.left)
        yield from _walk(expr.right)


def compile(expr):
    """Compile an AST into a reusable NumPy callable."""

    inputs = tuple(sorted(_inputs(expr)))

    def kernel(*args, **kwargs):
        if args and kwargs:
            raise TypeError("use positional or keyword inputs, not both")
        values = dict(zip(inputs, args)) if args else kwargs
        if set(values) != set(inputs):
            raise TypeError(f"expected inputs {inputs}")
        
        # Question: brother, you're just doing the same thing in 2 different ways. WHY!? 
        # I mean, you've demoed this and you're using this again here. WHY? 

        # Answer: the demo shows the API once; this callable reuses evaluate() so there
        # is one numerical execution path and no duplicated semantics to drift apart.
        return evaluate(expr, values)

    kernel.inputs = inputs
    kernel.ast = expr
    return kernel

__all__ = ["Expression", "Grammar", "ShapeError", "Vector", "compile", "evaluate", "parse", "vector"]
