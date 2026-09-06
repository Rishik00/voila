# Review questions, preserved and answered

The questions below are preserved verbatim from the review comments. Each one
has a direct answer immediately beneath it.

## `# Question: why is this a dataclass?`

`Expression` is a small immutable AST node. A frozen dataclass gives it named
fields, a useful representation, structural equality, and immutability without
boilerplate. It is appropriate here because an expression should not change
after it has been built.

## `# Question: here's another problem, what are the pathways for me to make an expression?`

There are two intended pathways: use normal Python operators on `Vector`
objects, such as `(x + y) * 2`, or call `parse("(x + y) * 2", {"x": 4, "y": 4})`.
Both pathways produce the same `Expression` AST.

## `# The way I see it, there's nothing stopping anyone from just making an expression via this class directly.`

That is true. `Expression` is public so the AST can be inspected and extended
during this proof of concept. Direct construction is useful for experiments,
but normal callers should use operators or `parse()`, which provide the valid
operation names and operand types.

## `# Not sure if that makes full sense here. I think that the expressions class should only be visible via vectors.`

That would be a reasonable stricter API: make the implementation class private
and expose only `Vector` plus `parse()`. For this MVP it remains public to make
the AST observable while the design is still being explored; the supported user
path is still through vectors and the parser.

## `# Question: and why is this public?`

`Expression` is public for AST inspection and extension. `Grammar` is public so
the parser can be tested or subclassed. The helper functions beginning with `_`
are private because they are implementation details rather than API surface.

## `# Question: does every vector need a compile function?`

No. The module-level `compile(expr)` is sufficient. `Vector.compile()` and
`Expression.compile()` are convenience methods that delegate to it, allowing a
leaf or a composed expression to use the same API. They can be removed later if
the API is intentionally narrowed.

## `# Question: why is this private?`

The parser implementation was private because callers only need `parse()`, not
the traversal machinery. In the current MVP, `Grammar` is public to make the
parser easy to inspect and extend; `_inputs`, `_numpy_value`, and `_walk` remain
private because they are execution helpers.

## `# Question: alright I was inspecting this, and found it rather...bizzare`

The unusual-looking part is the separation between Python's syntax tree and
the project's AST. Python parses source into `ast` nodes first; `Grammar` then
lowers only the supported nodes into `Vector` and `Expression`. This keeps
unsafe or unsupported Python syntax out of the evaluator.

## `# Question: how does this ast.NodeVisitor work? And how are you registeri`

`ast.NodeVisitor` dispatches `self.visit(node)` to a method named after the
node's class. For example, `ast.BinOp` calls `visit_BinOp`, `ast.Name` calls
`visit_Name`, and the root `ast.Expression` calls `visit_Expression`. No manual
registration is needed; the method names are the registration convention.

## `# Question: wait, are these even being called?`

Yes. `parse()` calls `Grammar(sizes).visit(tree)`, which starts at the root and
recursively dispatches to the `visit_*` methods. The runnable proof is in
`run.py`, where both operator-built and parsed expressions evaluate to
`[12, 16, 20, 24]`.

## `# Question: when I do x * 2, why are we not triggering visit_UnaryOp`

Because `x * 2` has two operands and Python represents it as `ast.BinOp`.
`visit_BinOp` handles it. `visit_UnaryOp` is only called for one-operand
operators such as `-x`.

## `# Question: why are we only checking for ast.USub`

`ast.USub` represents unary minus, which is the only unary operation supported
by this MVP. Other unary operators, such as unary plus or bitwise invert, are
rejected so the grammar stays explicit and small. More can be added deliberately
later.

## `# Question: hmm, so we're not making our own AST?`

We are. Python's `ast` tree is only the parser's input representation. The
project AST is made of `Vector` and `Expression` objects, and that is what
`evaluate()` and `compile()` consume.

## `# Question: what is this doing even?`

`_inputs(expr.left) | _inputs(expr.right)` recursively visits both branches of
an expression and unions their names. The result is the unique set of input
vectors needed to run the expression. The union prevents duplicate arguments
when a vector appears more than once.

## `# Question: brother, you're just doing the same thing in 2 different ways. WHY!?`

`_inputs()` and `_walk()` both recurse because the AST is a tree, but they have
different jobs. `_inputs()` returns unique names for compiled-callable argument
ordering. `_walk()` yields every node so `evaluate()` can validate each vector's
declared length. They cannot be replaced by the same result without losing one
of those semantics.

## `# I mean, you've demoed this and you're using this again here. WHY?`

The demo evaluates the expression once to show the API. The compiled callable
uses the same evaluator so it can be reused with different inputs without
duplicating numerical semantics. Keeping one execution path prevents the demo
and compiled form from drifting apart.
