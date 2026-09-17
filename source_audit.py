from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "source"
OUT = ROOT / "SOURCE_AUDIT.md"
KEYWORDS = re.compile(r"sqlite|sql|database|db_|connect\s*\(|commit\s*\(|rollback|close\s*\(|report|reports|pdf|open\s*\(|write_text|write_bytes|to_csv|save|backup|firebase|json\.dump|os\.replace|rename", re.I)

def source_files():
    return sorted(SRC.rglob("*.py"))

def context_lines(text, line_no, before=8, after=12):
    lines = text.splitlines()
    a = max(1, line_no - before)
    b = min(len(lines), line_no + after)
    return "\n".join(f"{i:04d}: {lines[i-1]}" for i in range(a, b + 1))

def main():
    parts = ["# Store Inventory source audit", "", f"Generated from `{SRC}` after CI patches.", ""]
    for path in source_files():
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        rel = path.relative_to(SRC)
        parts += [f"## {rel}", "", f"- Lines: {len(text.splitlines())}"]
        try:
            tree = ast.parse(text)
            funcs = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    funcs.append((node.lineno, node.end_lineno or node.lineno, node.name))
            parts.append("- Functions: " + ", ".join(f"{n}({a}-{b})" for a,b,n in sorted(funcs))[:12000])
        except Exception as exc:
            parts.append(f"- AST parse error: {exc}")
        matches = []
        for i, line in enumerate(text.splitlines(), 1):
            if KEYWORDS.search(line):
                matches.append(i)
        parts += ["", "### Relevant source locations", ""]
        seen = set()
        for i in matches:
            # one context block per nearby cluster
            cluster = next((x for x in seen if abs(x - i) <= 12), None)
            if cluster is not None:
                continue
            seen.add(i)
            parts.append("```text")
            parts.append(context_lines(text, i))
            parts.append("```")
        parts.append("")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
