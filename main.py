import numpy as np
import sympy as sp
from functools import reduce
import ast

dtype_conv = {
    'float64': np.float64
}

class ConvSymbol(sp.Symbol):
    def __new__(cls, name, shape=None, dtype=None, init_type: str = "ones"):
        obj = super().__new__(cls, name)
        obj.shape = shape
        obj.dtype = dtype
        obj.init_type = init_type
        
        return obj

    def realize(
        self, 
    ):
        target_dtype = dtype_conv[self.dtype]
        if self.init_type == "ones":
            self.data = np.ones(shape=self.shape, dtype=target_dtype)
        elif self.init_type == "zeros":
            self.data = np.zeros(shape=self.shape, dtype=target_dtype)
        else:
            raise TypeError("it's neither zeros nor ones, fix pls")

def compile_to_np(expr):
    args_list = []
    for arg in expr.args:
        arg.realize()
        args_list.append(arg.data)
    
    if expr.func == sp.Add:
        result = reduce(np.add, args_list)
        
    elif expr.func == sp.Mul:
        result = reduce(np.dot, args_list)

    return result

if __name__ == "__main__":
    x = ConvSymbol('x', shape=5, dtype='float64')
    y = ConvSymbol('y', shape=5, dtype='float64')
    z = ConvSymbol('z', shape=5, dtype='float64')

    expr1 = x + y + z
    expr2 = x * y
    
    tree1 = sp.srepr(expr1)
    tree2 = sp.srepr(expr2)

    print(compile_to_np(expr1))
    print(compile_to_np(expr2))