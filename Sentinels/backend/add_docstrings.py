import ast
import os

base_dir = r"c:\Users\wz\Desktop\ai-proj\Sentinels\backend\app\api\v1"

def add_docstrings(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    lines = source.splitlines()
    modified = False

    # We will traverse backward so inserting lines doesn't mess up line numbers for previous functions
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    functions.sort(key=lambda n: n.lineno, reverse=True)

    for node in functions:
        is_route = any(
            isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in ("get", "post", "put", "delete", "patch")
            for d in node.decorator_list
        )
        if is_route and not ast.get_docstring(node):
            # The body[0].lineno gives the first line of the function body
            insert_idx = node.body[0].lineno - 1
            # Build a simple docstring
            indent = "    "
            docstring = f'{indent}"""\n{indent}Endpoint for {node.name.replace("_", " ")}.\n{indent}"""'
            lines.insert(insert_idx, docstring)
            modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Added docstrings to {filepath}")

for filename in os.listdir(base_dir):
    if filename.endswith(".py"):
        add_docstrings(os.path.join(base_dir, filename))
