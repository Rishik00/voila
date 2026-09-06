import numpy as np
import sympy as sp

class Vector:
    def __init__(self, shape, dtype) -> None:
        self.shape = shape
        self.dtype = dtype

    def __add__(self, other):
        # return an expression with add as op
        return Expression(self, other, "add")


class Expression:
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op

    def __add__(self, other):
        return Expression(self, right, "add")

def vector(shape: tuple | int, dtype: str):
    # if not isinstance(shape, tuple) or not isinstance(shape, int):
    #     raise TypeError(f"Expected tuple/int, but got ts: {shape}")

    if dtype not in ['float', 'int', 'str']:
        raise TypeError(f"What the fuck is {dtype}?") 

    return Vector(shape, dtype)
