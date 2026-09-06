"""Runnable walkthrough for the voila MVP."""

import numpy as np

from voila import Vector, evaluate, parse


def main():
    # 1. Declare two fixed-size vector inputs.
    x = Vector("x", 4)
    y = Vector("y", 4)

    # 2. Build an expression with ordinary Python operators.
    expression = (x + y) * 2

    # 3. Evaluate it directly with NumPy arrays.
    result = evaluate(
        expression,
        {"x": np.array([1, 2, 3, 4]), "y": np.array([5, 6, 7, 8])},
    )
    print("operator AST:", expression)
    print("operator result:", result.tolist())

    # 4. Or parse the same expression from the supported grammar.
    parsed = parse("(x + y) * 2", {"x": 4, "y": 4})
    run = parsed.compile()
    print("parsed result:", run([1, 2, 3, 4], [5, 6, 7, 8]).tolist())


if __name__ == "__main__":
    main()
