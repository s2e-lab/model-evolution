import ast
from z3 import *

# Dynamically collect variable names
z3_vars = {}

# Mapping AST operations to Z3
ops = {
    ast.Or: Or,
    ast.And: And,
    ast.Not: Not,
    ast.BitOr: lambda *args: Or(*args),
    ast.BitAnd: lambda *args: And(*args),
    ast.Invert: Not
}

# Recursively convert an AST node to a Z3 expression
def ast_to_z3(node):
    if isinstance(node, ast.BoolOp):
        op = ops[type(node.op)]
        return op(*[ast_to_z3(v) for v in node.values])
    elif isinstance(node, ast.UnaryOp):
        op = ops[type(node.op)]
        return op(ast_to_z3(node.operand))
    elif isinstance(node, ast.Name):
        var_name = node.id
        if var_name not in z3_vars:
            z3_vars[var_name] = Bool(var_name)
        return z3_vars[var_name]
    elif isinstance(node, ast.Expr):
        return ast_to_z3(node.value)
    else:
        raise ValueError(f"Unsupported AST node: {ast.dump(node)}")

# ==== INPUT: boolean expression as string ====
input_expr = "((CONFIG_A | CONFIG_B) & (CONFIG_C | CONFIG_K)) | CONFIG_A | (CONFIG_J & (CONFIG_C | CONFIG_O))"

# Parse the input expression
tree = ast.parse(input_expr, mode='eval')
z3_expr = ast_to_z3(tree.body)

# Simplify using Z3
simplified_expr = simplify(z3_expr)

# Output
print("Discovered Variables:")
print(sorted(z3_vars.keys()))
print("\nOriginal Expression:")
print(input_expr)
print("\nSimplified Expression:")
print(simplified_expr)
