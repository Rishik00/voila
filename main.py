import numpy as np
import sympy as sp
from functools import reduce
import ast

dtype_conv = {
    'float': np.float64
}

class ConvSymbol(sp.Symbol):
    def __new__(cls, name, shape=None, dtype=None, ):
        obj = super().__new__(cls, name)
        obj.shape = shape
        obj.dtype = dtype
        return obj

    def realize(self):
        self.data = np.ones(shape=self.shape, dtype=dtype_conv[self.dtype])
        
x = ConvSymbol('x', shape=5, dtype='float')
y = ConvSymbol('y', shape=5, dtype='float')
z = ConvSymbol('z', shape=5, dtype='float')
expr = x + y + z
tree = sp.srepr(expr)

print(tree)
# v = {}

if expr.func == sp.Add:
    for arg in expr.args:
        arg.realize()

    print(reduce(np.add, [x.data, y.data, z.data]))
