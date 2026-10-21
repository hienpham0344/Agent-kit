#!/usr/bin/env python3
"""
AST Code Complexity & Signature Scanner for Agents-kit
Scans Python codebases for cyclomatic complexity, function signatures, and class hierarchies.
"""

import ast
import sys
from pathlib import Path

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions = []
        self.imports = []
        self.complexity = 1

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        mod = node.module or ""
        for alias in node.names:
            self.imports.append(f"{mod}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        bases = [ast.unparse(b) for b in node.bases]
        self.classes.append({"name": node.name, "methods": methods, "bases": bases, "line": node.lineno})
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        args = [a.arg for a in node.args.args]
        self.functions.append({"name": node.name, "args": args, "line": node.lineno})
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

def analyze_file(filepath: Path) -> dict:
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
        visitor = CodeAnalyzer()
        visitor.visit(tree)
        return {
            "file": str(filepath.name),
            "classes": visitor.classes,
            "functions": visitor.functions,
            "imports_count": len(visitor.imports),
            "complexity": visitor.complexity
        }
    except Exception as e:
        return {"file": str(filepath.name), "error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ast_analyzer.py <python_file_or_directory>")
        sys.exit(1)

    target = Path(sys.argv[1])
    files = [target] if target.is_file() else list(target.rglob("*.py"))

    print(f"\n🔍 AST Code Structure & Complexity Scan ({len(files)} files)")
    print("=" * 60)
    for f in files[:20]:
        res = analyze_file(f)
        if "error" in res:
            print(f"⚠️ {res['file']}: {res['error']}")
        else:
            print(f"📄 {res['file']} (Cyclomatic Complexity: {res['complexity']})")
            if res['classes']:
                for c in res['classes']:
                    print(f"   └── Class: {c['name']} (Bases: {', '.join(c['bases']) or 'None'}) -> {len(c['methods'])} methods")
            if res['functions']:
                for fn in res['functions'][:5]:
                    print(f"   └── def {fn['name']}({', '.join(fn['args'])}) [Line {fn['line']}]")
                if len(res['functions']) > 5:
                    print(f"   └── ... and {len(res['functions']) - 5} more functions")

if __name__ == "__main__":
    main()
