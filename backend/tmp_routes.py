import ast
import os
db_path = os.path.join(r"e:\Swasthya-Sampark---Emergency-Response-Data-Management-System-main\backend", "app.py")
with open(db_path, "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)

routes = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr == "route":
                    path = "unknown"
                    if decorator.args:
                        path = decorator.args[0].value
                    routes.append((node.name, path))

with open("routes.txt", "w") as f:
    for name, path in routes:
        f.write(f"{name}: {path}\n")
