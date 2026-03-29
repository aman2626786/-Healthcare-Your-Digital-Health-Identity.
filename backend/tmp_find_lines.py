import ast
import os
db_path = os.path.join(r"e:\Swasthya-Sampark---Emergency-Response-Data-Management-System-main\backend", "app.py")
with open(db_path, "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "scan_qr":
        print(f"StartLine: {node.lineno}")
        print(f"EndLine: {node.end_lineno}")
