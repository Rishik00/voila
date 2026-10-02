import numpy as np
import sympy as sp
import ast, dis
import astpretty

class ConvSymbol(sp.Symbol):
    def __new__(cls, name, shape, dtype):
        obj = super().__new__(cls, name)
        obj.shape = shape
        obj.dtype = dtype
        obj.data = np.ones(shape=shape, dtype=np.float16)

        return obj

class Parser(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        
        if node.func.id == 'Add':
            new_args = []
            for arg in node.args:
                new_args.append(
                    ast.Attribute(value=ast.Name(id=arg.args[0].value, ctx=ast.Load()), attr='data', ctx=ast.Load()),
                )
            
            node = ast.Call(
                func=ast.Name(id="sum", ctx=ast.Load()),
                args=[
                    ast.List(
                        elts=new_args,
                        ctx=ast.Load()
                    )
                ],
                keywords=[]
            )
    
        return node

def csymbol(var: str, dtype: str, shape):
    return ConvSymbol(
        var, shape=shape, dtype=dtype, 
    )

def eval_expression(expr, dump: bool = False):
    parser = Parser()    
    tree = ast.parse(sp.srepr(expr))
    namespace = {
        str(symbol): symbol for symbol in expr.free_symbols
    }

    new_tree = parser.visit(tree)
    expr_tree = ast.Expression(body=new_tree.body[0].value)
    expr_tree = ast.fix_missing_locations(expr_tree)

    if dump == True:
        astpretty.pprint(
            tree, show_offsets=False, indent=2
        )
        astpretty.pprint(
            new_tree, show_offsets=False, indent=2
        )

    code = compile(expr_tree, "<transformed>", "eval")

    if dump == True:
        dis.dis(code)

    print("Final expression: ", ast.unparse(tree))
    res = eval(code, namespace)
    return res

__all__ = ["ConvSymbol", "csymbol", "eval_expression"]