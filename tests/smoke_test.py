"""Checagens locais leves; não conectam ao banco nem importam a planilha real."""
from pathlib import Path
import ast
ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "app").glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
for required in ["app/main.py", "app/models.py", "app/security.py", "app/static/index.html", "app/static/app.js", "app/static/app.css", "requirements.txt", "README.md"]:
    assert (ROOT / required).is_file(), f"Arquivo ausente: {required}"
html = (ROOT / "app/static/index.html").read_text(encoding="utf-8")
assert "BI Rede Duarte" in html and "/static/app.js" in html
js = (ROOT / "app/static/app.js").read_text(encoding="utf-8")
assert "/api/admin/imports/confirm" in js and "data-detail" in js
print("Smoke test estrutural: OK")
