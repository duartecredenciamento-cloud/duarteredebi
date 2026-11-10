"""Checagens leves da estrutura e sintaxe; não acessam o banco nem dados reais."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "app").glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
for required in [
    "app/main.py", "app/analytics.py", "app/models.py", "app/security.py",
    "app/static/index.html", "app/static/app.js", "app/static/app.css",
    "app/static/logo.png", "requirements.txt", "railway.json", "README.md",
]:
    assert (ROOT / required).is_file(), f"Arquivo ausente: {required}"
html = (ROOT / "app/static/index.html").read_text(encoding="utf-8")
assert "BI Rede Duarte" in html and "/static/app.js" in html
assert 'id="kSpecialties"' in html and 'id="kStates"' in html and 'id="stateProviders"' in html
assert 'specialtiesBottom' not in html and 'COBERTURA DE UF' in html
assert 'id="statuses"' not in html
js = (ROOT / "app/static/app.js").read_text(encoding="utf-8")
assert "/api/admin/imports/confirm" in js and "data-detail" in js
assert "/api/admin/data-audit" in js and "dashboardFilters" in js
assert "by_state" in js and "TIPO ESPECIALIDADE" in js and "sidebarToggle" in js
css = (ROOT / "app/static/app.css").read_text(encoding="utf-8")
assert "[hidden]{display:none!important}" in css
print("Smoke test estrutural: OK")
