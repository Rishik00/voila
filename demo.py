"""SymPy -> NumPy lowering demo for vector add and scalar multiplication.

This is intentionally a learning spike, not the final Voila architecture.
Run it with:

    python demo.py
"""

from __future__ import annotations

from functools import reduce

import numpy as np
import sympy as sp


# ---------------------------------------------------------------------------
# 1. SymPy symbols and metadata
# ---------------------------------------------------------------------------
#
# SymPy sees x and y as symbolic operands. For this direct-lowering experiment,
# vector-specific information lives in a separate metadata dictionary.

x, y = sp.symbols("x y")

VECTOR_METADATA = {
    x: {"shape": (4,), "dtype": np.dtype("float32")},
    y: {"shape": (4,), "dtype": np.dtype("float32")},
}


# ---------------------------------------------------------------------------
# 2. Inspecting the SymPy IR
# ---------------------------------------------------------------------------

def print_tree(expr: sp.Basic, depth: int = 0) -> None:
    """Recursively display the node class (`func`) and child nodes (`args`)."""

    indent = "  " * depth
    print(
        f"{indent}{expr!s:<18} "
        f"func={expr.func.__name__:<8} "
        f"args={expr.args}"
    )
    for arg in expr.args:
        print_tree(arg, depth + 1)


def inspect_case(label: str, expr: sp.Basic) -> None:
    """Show three useful views of one SymPy expression."""

    print(f"\n{label}: {expr}")
    print(f"srepr: {sp.srepr(expr)}")
    print("tree:")
    print_tree(expr)
    print(
        "preorder:",
        [f"{node.func.__name__}({node})" for node in sp.preorder_traversal(expr)],
    )


# ---------------------------------------------------------------------------
# 3. Semantic validation
# ---------------------------------------------------------------------------

# Review: are we sure sp.Basic is correct? 
def infer_type(expr: sp.Basic, metadata: dict) -> dict:
    """Infer scalar/vector kind, shape, and dtype for the MVP operations."""

    if isinstance(expr, sp.Symbol):
        if expr not in metadata:
            raise TypeError(f"unknown symbol {expr!s}; runtime scalars are not in this demo")
        return {
            "kind": "vector",
            "shape": metadata[expr]["shape"],
            "dtype": metadata[expr]["dtype"],
        }

    if expr.is_Number:
        return {"kind": "scalar", "shape": (), "dtype": None}

    if expr.func is sp.Add:
        operands = [infer_type(arg, metadata) for arg in expr.args]
        if any(operand["kind"] != "vector" for operand in operands):
            raise TypeError("Add only accepts vectors in this MVP")
        if any(operand["shape"] != operands[0]["shape"] for operand in operands[1:]):
            raise TypeError("Add operands must have the same shape")
        return {
            "kind": "vector",
            "shape": operands[0]["shape"],
            "dtype": np.result_type(*(operand["dtype"] for operand in operands)),
        }

    if expr.func is sp.Mul:
        operands = [infer_type(arg, metadata) for arg in expr.args]
        vectors = [operand for operand in operands if operand["kind"] == "vector"]
        if len(vectors) != 1:
            raise TypeError("Mul requires exactly one vector; vector*vector is unsupported")
        return {
            "kind": "vector",
            "shape": vectors[0]["shape"],
            "dtype": vectors[0]["dtype"],
        }

    raise TypeError(f"unsupported SymPy node: {expr.func.__name__}")


# ---------------------------------------------------------------------------
# 4. Tiny NumPy backend
# ---------------------------------------------------------------------------
#
# Each supported SymPy object gets one lowering function. The dictionary is the
# backend's dispatch table. This is direct SymPy lowering: there is no Voila IR.

def lower_symbol(expr: sp.Symbol, bindings: dict):
    return bindings[expr]


def lower_number(expr: sp.Number, bindings: dict):
    del bindings
    if expr.is_Integer:
        return int(expr)
    return float(expr)


def lower_add(expr: sp.Add, bindings: dict):
    values = [lower_numpy(arg, bindings) for arg in expr.args]
    return reduce(np.add, values)


def lower_mul(expr: sp.Mul, bindings: dict):
    values = [lower_numpy(arg, bindings) for arg in expr.args]
    return reduce(np.multiply, values)


NUMPY_HANDLERS = {
    sp.Symbol: lower_symbol,
    sp.Add: lower_add,
    sp.Mul: lower_mul,
}


def lower_numpy(expr: sp.Basic, bindings: dict):
    """Recursively evaluate one supported SymPy node with NumPy."""

    if expr.is_Number:
        return lower_number(expr, bindings)

    handler = NUMPY_HANDLERS.get(expr.func)
    if handler is None:
        raise TypeError(f"NumPy backend does not support {expr.func.__name__}")
    return handler(expr, bindings)


def run_numpy(expr: sp.Basic, bindings: dict, metadata: dict):
    """Validate a symbolic expression and execute it with the NumPy backend."""

    result_type = infer_type(expr, metadata)

    prepared = {}
    for symbol in expr.free_symbols:
        if symbol not in bindings:
            raise KeyError(f"missing runtime value for {symbol!s}")
        array = np.asarray(bindings[symbol])
        expected = metadata[symbol]
        if array.shape != expected["shape"]:
            raise ValueError(
                f"{symbol!s} has shape {array.shape}, expected {expected['shape']}"
            )
        if array.dtype != expected["dtype"]:
            raise TypeError(
                f"{symbol!s} has dtype {array.dtype}, expected {expected['dtype']}"
            )
        prepared[symbol] = array

    result = np.asarray(lower_numpy(expr, prepared))
    assert result.shape == result_type["shape"]
    return result


# ---------------------------------------------------------------------------
# 5. Four expression shapes to study
# ---------------------------------------------------------------------------


def main() -> None:

    CASES = {
        "1. vector add": x + y,
        "2. scalar multiply": 3 * x,
        "3. nested add/multiply": x + 3 * y,
        "4. scalar over expression": 2 * (x + y),
    }

    x_value = np.array([1, 2, 3, 4], dtype=np.float32)
    y_value = np.array([10, 20, 30, 40], dtype=np.float32)
    bindings = {x: x_value, y: y_value}

    for label, expr in CASES.items():
        inspect_case(label, expr)
        print("inferred:", infer_type(expr, VECTOR_METADATA))
        print("result:", run_numpy(expr, bindings, VECTOR_METADATA))

    print("\nUnsupported case: x * y")
    try:
        infer_type(x * y, VECTOR_METADATA)
    except TypeError as error:
        print("correctly rejected:", error)


if __name__ == "__main__":
    main()
