from __future__ import annotations
import csv, hashlib, io, json, os, re, secrets, unicodedata, tempfile
from itertools import chain
from starlette.background import BackgroundTask
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session as DBSession
from .config import BASE_DIR, COOKIE_SECURE, MAX_UPLOAD_BYTES, SESSION_SECRET, STAGING_DIR
from .database import Base, SessionLocal, engine
from .models import AuditLog, ImportBatch, LoginThrottle, ProviderRecord, Session, User, utcnow
from .security import COOKIE_NAME, create_session, current_user, digits, hash_password, require_admin, signed_token, valid_cpf, verify_password

app = FastAPI(title="BI Rede Duarte", version="1.0.0", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")

class LoginBody(BaseModel):
    cpf: str
    password: str
class UserBody(BaseModel):
    cpf: str
    name: str = Field(min_length=2, max_length=180)
    password: str = Field(min_length=12, max_length=200)
    role: str = "consulta"
class RecordBody(BaseModel):
    data: dict
class ConfirmImport(BaseModel):
    token: str
    confirm: bool
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=200)
class PasswordReset(BaseModel):
    new_password: str = Field(min_length=12, max_length=200)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
def audit(db, user_id, action, detail=""):
    db.add(AuditLog(user_id=user_id, action=action, detail=str(detail)[:300]))
def norm(value):
    text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    return "".join(c for c in text if not unicodedata.combining(c))
def header_key(value):
    return re.sub(r"[^a-z0-9]", "", norm(value).replace("\n", " "))
def clean_cell(value):
    if value is None: return ""
    if isinstance(value, datetime): return value.date().isoformat()
    if hasattr(value, "isoformat") and not isinstance(value, str):
        try: return value.isoformat()
        except Exception: pass
    return str(value).strip()
def first(data, *names):
    normalized = {header_key(k): v for k, v in data.items()}
    for name in names:
        if header_key(name) in normalized: return str(normalized[header_key(name)] or "").strip()
    return ""
def pack_record(data):
    return ProviderRecord(
        data=data,
        business_name=first(data, "RAZÃO SOCIAL"),
        trade_name=first(data, "NOME FANTASIA", "NOME FANTASIA "),
        tax_id=first(data, "CNPJCPF", "CNPJ/CPF", "CNPJ CPF"),
        specialty=first(data, "ESPECIALIDADE"),
        service=first(data, "SERVIÇO", "SERVICO"),
        category=first(data, "TIPO PRESTADOR (CATEGORIA)"),
        status=first(data, "STATUS"),
        municipality=first(data, "MUNICÍPIO", "MUNICIPIO"),
        uf=first(data, "UF"), region=first(data, "REGIÃO (ZONA)", "REGIAO (ZONA)"),
        priority=first(data, "PRIORIDADE"), classification=first(data, "CLASSIFICAÇÃO", "CLASSIFICACAO"),
        cnes=first(data, "CNES"), search_text=" ".join(str(v) for v in data.values() if v))
def as_user(user):
    return {"id": user.id, "name": user.name, "cpf": f"***.***.***-{user.cpf[-2:]}", "role": user.role}
SENSITIVE = {header_key(x) for x in ["OBSERVAÇÃO INTERNA", "CNPJCPF", "CNPJ/CPF", "NOME DO CONTATO - RESPONSÁVEL", "NOME DO CONTATO - COMERCIAL", "E-MAIL - RESPONSÁVEL", "E-MAIL - COMERCIAL", "E-MAIL - 1", "E-MAIL - 2", "TELEFONE 1", "TELEFONE 2", "TELEFONE 3", "TELEFONE 4", "CELULAR 1", "CELULAR 2"]}
def safe_record(row, admin=False):
    data = dict(row.data or {})
    if not admin:
        for k in list(data):
            if header_key(k) in SENSITIVE: data.pop(k, None)
    return {"id": row.id, "data": data, "business_name": row.business_name, "trade_name": row.trade_name,
            "specialty": row.specialty, "service": row.service, "category": row.category,
            "status": row.status, "municipality": row.municipality, "uf": row.uf,
            "region": row.region, "priority": row.priority, "classification": row.classification, "cnes": row.cnes}
def by_dimension(db, column, limit=10):
    stmt = select(column.label("label"), func.count(ProviderRecord.id).label("count")).where(ProviderRecord.active.is_(True), column != "").group_by(column).order_by(func.count(ProviderRecord.id).desc()).limit(limit)
    return [{"label": x.label or "Não informado", "count": x.count} for x in db.execute(stmt)]
def require_user(request: Request, db: DBSession = Depends(get_db)):
    return current_user(request, db)
def admin_user(user: User = Depends(require_user)):
    require_admin(user)
    return user
def editor_user(user: User = Depends(require_user)):
    if user.role not in {"admin", "operador"}:
        raise HTTPException(403, "Ação restrita aos perfis de manutenção.")
    return user

@app.on_event("startup")
def startup():
    if not SESSION_SECRET and os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise RuntimeError("Defina SESSION_SECRET antes de iniciar em produção.")
    Base.metadata.create_all(bind=engine)
    cpf, password, name = os.getenv("ADMIN_BOOTSTRAP_CPF", ""), os.getenv("ADMIN_BOOTSTRAP_PASSWORD", ""), os.getenv("ADMIN_BOOTSTRAP_NAME", "Administrador Master")
    if cpf and password:
        with SessionLocal() as db:
            if db.scalar(select(User.id).where(User.role == "admin").limit(1)) is None:
                cleaned = digits(cpf)
                if not valid_cpf(cleaned): raise RuntimeError("ADMIN_BOOTSTRAP_CPF deve conter CPF válido.")
                if len(password) < 12: raise RuntimeError("ADMIN_BOOTSTRAP_PASSWORD deve ter ao menos 12 caracteres.")
                db.add(User(cpf=cleaned, name=name, password_hash=hash_password(password), role="admin"))
                db.commit()

@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse(BASE_DIR / "app" / "static" / "index.html")
@app.get("/api/health")
def health(): return {"ok": True, "service": "BI Rede Duarte"}
@app.post("/api/login")
def login(body: LoginBody, request: Request, db: DBSession = Depends(get_db)):
    cpf = digits(body.cpf)
    remote = request.client.host if request.client else "unknown"
    throttle_key = hashlib.sha256(f"{cpf}|{remote}".encode()).hexdigest()
    throttle = db.get(LoginThrottle, throttle_key)
    now = utcnow()
    if throttle and throttle.locked_until:
        locked_until = throttle.locked_until.replace(tzinfo=timezone.utc) if throttle.locked_until.tzinfo is None else throttle.locked_until
        if locked_until > now: raise HTTPException(429, "Muitas tentativas. Aguarde 15 minutos e tente novamente.")
    user = db.scalar(select(User).where(User.cpf == cpf))
    if not user or not user.active or not verify_password(body.password, user.password_hash):
        if not throttle:
            throttle = LoginThrottle(key=throttle_key, failures=0, window_started=now)
            db.add(throttle)
        window_started = throttle.window_started.replace(tzinfo=timezone.utc) if throttle.window_started.tzinfo is None else throttle.window_started
        if (now - window_started).total_seconds() > 900:
            throttle.failures = 0; throttle.window_started = now; throttle.locked_until = None
        throttle.failures += 1
        if throttle.failures >= 8: throttle.locked_until = now + timedelta(minutes=15)
        db.commit()
        if throttle.failures >= 8: raise HTTPException(429, "Muitas tentativas. Aguarde 15 minutos e tente novamente.")
        raise HTTPException(401, "CPF ou senha inválidos.")
    if throttle: db.delete(throttle)
    token, expires = create_session(db, user); audit(db, user.id, "LOGIN")
    db.commit()
    response = {"user": as_user(user)}
    from fastapi.responses import JSONResponse
    out = JSONResponse(response)
    out.set_cookie(COOKIE_NAME, signed_token(token), httponly=True, secure=COOKIE_SECURE, samesite="strict", expires=expires, path="/")
    return out
@app.get("/api/me")
def me(user: User = Depends(require_user)): return {"user": as_user(user)}
@app.post("/api/logout")
def logout(request: Request, user: User = Depends(require_user), db: DBSession = Depends(get_db)):
    raw = request.cookies.get(COOKIE_NAME, "").split(".", 1)[0]
    db.query(Session).filter(Session.token_hash == hashlib.sha256(raw.encode()).hexdigest()).delete()
    audit(db, user.id, "LOGOUT"); db.commit()
    from fastapi.responses import JSONResponse
    out = JSONResponse({"ok": True}); out.delete_cookie(COOKIE_NAME, path="/"); return out
@app.post("/api/password")
def change_password(body: PasswordChange, request: Request, user: User = Depends(require_user), db: DBSession = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash): raise HTTPException(401, "Senha atual incorreta.")
    user.password_hash = hash_password(body.new_password)
    db.query(Session).filter(Session.user_id == user.id).delete()
    audit(db, user.id, "CHANGE_PASSWORD"); db.commit()
    from fastapi.responses import JSONResponse
    out = JSONResponse({"ok": True, "message": "Senha atualizada. Entre novamente."}); out.delete_cookie(COOKIE_NAME, path="/"); return out
@app.get("/api/dashboard")
def dashboard(user: User = Depends(require_user), db: DBSession = Depends(get_db)):
    active = ProviderRecord.active.is_(True)
    total = db.scalar(select(func.count(ProviderRecord.id)).where(active)) or 0
    return {"total_records": total,
            "active_status": db.scalar(select(func.count(ProviderRecord.id)).where(active, func.lower(ProviderRecord.status).in_(["ativo", "ativa", "atualizado", "credenciado"]))) or 0,
            "priority": db.scalar(select(func.count(ProviderRecord.id)).where(active, func.lower(ProviderRecord.priority).in_(["sim", "alta", "prioritário", "prioritario"]))) or 0,
            "municipalities": db.scalar(select(func.count(func.distinct(ProviderRecord.municipality))).where(active, ProviderRecord.municipality != "")) or 0,
            "by_region": by_dimension(db, ProviderRecord.region), "by_specialty": by_dimension(db, ProviderRecord.specialty),
            "by_status": by_dimension(db, ProviderRecord.status, 8), "by_uf": by_dimension(db, ProviderRecord.uf, 12),
            "role": user.role}
@app.get("/api/records")
def records(q: str = "", specialty: str = "", municipality: str = "", uf: str = "", status: str = "", service: str = "", priority: str = "", page: int = 1, page_size: int = 25,
            user: User = Depends(require_user), db: DBSession = Depends(get_db)):
    if page < 1 or page > (20000 if user.role == "admin" else 20): raise HTTPException(400, "Limite de paginação atingido. Refine os filtros ou peça apoio ao administrador.")
    page_size = min(max(page_size, 1), 50)
    if user.role != "admin" and not any(str(x).strip() for x in (q, specialty, municipality, uf, status, service, priority)):
        raise HTTPException(400, "Informe ao menos um termo ou filtro antes de consultar a base.")
    if user.role != "admin" and len(q.strip()) == 1:
        raise HTTPException(400, "Digite ao menos 2 caracteres para pesquisar.")
    if len(q.strip()) == 1:
        raise HTTPException(400, "Digite ao menos 2 caracteres para pesquisar.")
    page_size = min(page_size, 50)
    stmt = select(ProviderRecord).where(ProviderRecord.active.is_(True))
    if q.strip():
        term = q.strip()[:120]
        if len(term) < 2: raise HTTPException(400, "Digite ao menos 2 caracteres para pesquisar.")
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = escaped + "%"
        stmt = stmt.where(or_(ProviderRecord.business_name.ilike(like, escape="\\"), ProviderRecord.trade_name.ilike(like, escape="\\"), ProviderRecord.tax_id.ilike(like, escape="\\"), ProviderRecord.cnes.ilike(like, escape="\\"), ProviderRecord.specialty.ilike(like, escape="\\"), ProviderRecord.search_text.ilike("%" + escaped + "%", escape="\\")))
    for col, value in [(ProviderRecord.specialty, specialty), (ProviderRecord.municipality, municipality), (ProviderRecord.uf, uf), (ProviderRecord.status, status), (ProviderRecord.service, service), (ProviderRecord.priority, priority)]:
        if value.strip(): stmt = stmt.where(col.ilike("%" + value.strip()[:120] + "%"))
    count = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(ProviderRecord.business_name, ProviderRecord.id).offset((page-1)*page_size).limit(page_size)).all()
    audit(db, user.id, "SEARCH", f"q={q[:30]} page={page} results={len(rows)}"); db.commit()
    pages = (count + page_size - 1)//page_size
    if user.role != "admin": pages = min(pages, 20)
    return {"items": [safe_record(row, user.role == "admin") for row in rows], "total": count, "page": page, "page_size": page_size, "pages": pages}
@app.get("/api/records/{record_id}")
def record_detail(record_id: int, user: User = Depends(require_user), db: DBSession = Depends(get_db)):
    row = db.get(ProviderRecord, record_id)
    if not row or not row.active: raise HTTPException(404, "Registro não encontrado.")
    audit(db, user.id, "VIEW_RECORD", f"record_id={record_id}"); db.commit()
    return safe_record(row, user.role == "admin")
@app.post("/api/admin/records")
def create_record(body: RecordBody, user: User = Depends(editor_user), db: DBSession = Depends(get_db)):
    row = pack_record({str(k): clean_cell(v) for k, v in body.data.items()})
    db.add(row); db.flush(); audit(db, user.id, "CREATE_RECORD", f"record_id={row.id}"); db.commit()
    return {"id": row.id}
@app.put("/api/admin/records/{record_id}")
def update_record(record_id: int, body: RecordBody, user: User = Depends(editor_user), db: DBSession = Depends(get_db)):
    row = db.get(ProviderRecord, record_id)
    if not row or not row.active: raise HTTPException(404, "Registro não encontrado.")
    fresh = pack_record({str(k): clean_cell(v) for k, v in body.data.items()})
    for key in ("data", "business_name", "trade_name", "tax_id", "specialty", "service", "category", "status", "municipality", "uf", "region", "priority", "classification", "cnes", "search_text"):
        setattr(row, key, getattr(fresh, key))
    audit(db, user.id, "UPDATE_RECORD", f"record_id={record_id}"); db.commit(); return {"ok": True}
@app.delete("/api/admin/records/{record_id}")
def deactivate_record(record_id: int, user: User = Depends(admin_user), db: DBSession = Depends(get_db)):
    row = db.get(ProviderRecord, record_id)
    if not row or not row.active: raise HTTPException(404, "Registro não encontrado.")
    row.active = False; audit(db, user.id, "DEACTIVATE_RECORD", f"record_id={record_id}"); db.commit(); return {"ok": True}

def excel_rows(content: bytes):
    try:
        from openpyxl import load_workbook
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc: raise HTTPException(400, "Não foi possível ler o XLSX enviado.") from exc
    sheet = next((s for s in workbook.worksheets if norm(s.title) == "banco rede"), workbook.worksheets[-1])
    values = sheet.iter_rows(values_only=True)
    header = next(values, None)
    if not header: raise HTTPException(400, "A planilha está vazia.")
    headers = [clean_cell(x) for x in header]
    if not any(header_key(x) in {"razaosocial", "especialidade", "municipio"} for x in headers):
        raise HTTPException(400, "Não reconheci os cabeçalhos da aba de dados.")
    try:
        for line, cells in enumerate(values, start=2):
            data = {headers[i] or f"COLUNA_{i+1}": clean_cell(value) for i, value in enumerate(cells[:len(headers)])}
            yield line, data
    finally:
        workbook.close()
@app.post("/api/admin/imports/preview")
async def import_preview(file: UploadFile = File(...), user: User = Depends(admin_user), db: DBSession = Depends(get_db)):
    filename = Path(file.filename or "base.xlsx").name
    if not filename.lower().endswith(".xlsx"): raise HTTPException(400, "Envie uma planilha .xlsx.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES: raise HTTPException(413, "O arquivo excede 25 MB.")
    count = blank_rows = 0
    sample = []
    for _, data in excel_rows(content):
        if not any(data.values()):
            blank_rows += 1
            continue
        count += 1
        if len(sample) < 5: sample.append(data)
    if not count: raise HTTPException(400, "Não há registros preenchidos para importar.")
    fingerprint = hashlib.sha256(content).hexdigest()
    duplicate = db.scalar(select(ImportBatch.id).where(ImportBatch.fingerprint == fingerprint)) is not None
    token = secrets.token_urlsafe(24)
    if not duplicate:
        (STAGING_DIR / f"{token}.json").write_text(json.dumps({"user_id": user.id, "filename": filename, "fingerprint": fingerprint, "blank_rows": blank_rows}, ensure_ascii=False), encoding="utf-8")
        (STAGING_DIR / f"{token}.xlsx").write_bytes(content)
    return {"token": "" if duplicate else token, "filename": filename, "records": count, "blank_rows": blank_rows, "duplicate_file": duplicate, "sample": sample, "warning": "A prévia não grava registros. Linhas preenchidas serão preservadas individualmente."}
@app.post("/api/admin/imports/confirm")
def confirm_import(body: ConfirmImport, user: User = Depends(admin_user), db: DBSession = Depends(get_db)):
    if not body.confirm: raise HTTPException(400, "Confirme explicitamente a importação.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{20,80}", body.token): raise HTTPException(400, "Prévia inválida.")
    path = STAGING_DIR / f"{body.token}.json"
    if not path.is_file(): raise HTTPException(410, "Prévia expirada. Envie novamente a planilha.")
    staged = json.loads(path.read_text(encoding="utf-8"))
    workbook_path = STAGING_DIR / f"{body.token}.xlsx"
    if staged.get("user_id") != user.id: raise HTTPException(403, "Prévia criada por outro administrador.")
    if not workbook_path.is_file(): raise HTTPException(410, "Planilha da prévia não está mais disponível; envie novamente.")
    if db.scalar(select(ImportBatch.id).where(ImportBatch.fingerprint == staged["fingerprint"])):
        raise HTTPException(409, "Este arquivo já foi importado.")
    count = 0
    try:
        for _, data in excel_rows(workbook_path.read_bytes()):
            if not any(data.values()): continue
            db.add(pack_record(data)); count += 1
            if count % 1000 == 0: db.flush()
        db.add(ImportBatch(filename=staged["filename"], fingerprint=staged["fingerprint"], row_count=count, blank_rows=staged.get("blank_rows", 0), imported_by=user.id))
        audit(db, user.id, "IMPORT_XLSX", f"{staged['filename']}: {count} linhas")
        db.commit()
    except Exception:
        db.rollback(); raise
    path.unlink(missing_ok=True); workbook_path.unlink(missing_ok=True)
    return {"ok": True, "imported": count}
@app.get("/api/admin/export.csv")
def export_csv(user: User = Depends(admin_user), db: DBSession = Depends(get_db)):
    output = io.StringIO(newline="")
    rows = db.scalars(select(ProviderRecord).where(ProviderRecord.active.is_(True)).order_by(ProviderRecord.id)).yield_per(1000)
    fieldnames = []
    # Use the original source fields; append internal ID so repeated rows remain distinguishable.
    for row in rows:
        if not fieldnames:
            fieldnames = list((row.data or {}).keys()) + ["ID INTERNO"]
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore"); writer.writeheader()
        writer.writerow({**(row.data or {}), "ID INTERNO": row.id})
    audit(db, user.id, "EXPORT_CSV", "Base completa ativa"); db.commit()
    payload = "\ufeff" + output.getvalue()
    return StreamingResponse(iter([payload]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=BI_REDE_DUARTE_backup.csv"})
@app.get("/api/admin/export.xlsx")
def export_xlsx(user: User = Depends(admin_user), db: DBSession = Depends(get_db)):
    from openpyxl import Workbook
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("BANCO REDE")
    rows = iter(db.scalars(select(ProviderRecord).where(ProviderRecord.active.is_(True)).order_by(ProviderRecord.id)).yield_per(1000))
    first_row = next(rows, None)
    if first_row:
        fields = list((first_row.data or {}).keys())
        sheet.append(fields + ["ID INTERNO"])
        for row in chain([first_row], rows):
            data = row.data or {}
            sheet.append([data.get(field, "") for field in fields] + [row.id])
    else:
        sheet.append(["ID INTERNO"])
    handle, name = tempfile.mkstemp(prefix="bi-rede-duarte-", suffix=".xlsx")
    os.close(handle)
    workbook.save(name)
    audit(db, user.id, "EXPORT_XLSX", "Base completa ativa"); db.commit()
    path = Path(name)
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="BI_REDE_DUARTE_backup.xlsx", background=BackgroundTask(lambda: path.unlink(missing_ok=True)))
@app.get("/api/admin/users")
def list_users(user: User = Depends(admin_user), db: DBSession = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.name)).all()
    return [{"id": u.id, "name": u.name, "cpf": f"***.***.***-{u.cpf[-2:]}", "role": u.role, "active": u.active, "created_at": u.created_at.isoformat()} for u in users]
@app.post("/api/admin/users")
def create_user(body: UserBody, user: User = Depends(admin_user), db: DBSession = Depends(get_db)):
    cpf = digits(body.cpf)
    if not valid_cpf(cpf): raise HTTPException(400, "CPF inválido.")
    if body.role not in {"consulta", "operador"}: raise HTTPException(400, "Perfil inválido; use consulta ou operador.")
    if db.scalar(select(User.id).where(User.cpf == cpf)): raise HTTPException(409, "Já existe usuário com esse CPF.")
    new = User(cpf=cpf, name=body.name.strip(), password_hash=hash_password(body.password), role=body.role)
    db.add(new); db.flush(); audit(db, user.id, "CREATE_USER", f"user_id={new.id} role={new.role}"); db.commit(); return {"id": new.id}
@app.post("/api/admin/users/{user_id}/password")
def admin_reset_password(user_id: int, body: PasswordReset, user: User = Depends(admin_user), db: DBSession = Depends(get_db)):
    target = db.get(User, user_id)
    if not target: raise HTTPException(404, "Usuário não encontrado.")
    target.password_hash = hash_password(body.new_password)
    db.query(Session).filter(Session.user_id == target.id).delete()
    audit(db, user.id, "RESET_USER_PASSWORD", f"user_id={target.id}"); db.commit(); return {"ok": True}
@app.patch("/api/admin/users/{user_id}/status")
def change_user_status(user_id: int, active: bool, user: User = Depends(admin_user), db: DBSession = Depends(get_db)):
    target = db.get(User, user_id)
    if not target: raise HTTPException(404, "Usuário não encontrado.")
    if target.id == user.id and not active: raise HTTPException(400, "Não é possível desativar a própria conta.")
    target.active = active
    if not active: db.query(Session).filter(Session.user_id == target.id).delete()
    audit(db, user.id, "USER_STATUS", f"user_id={target.id} active={active}"); db.commit(); return {"ok": True}
@app.get("/api/admin/audit")
def audit_history(limit: int = 100, user: User = Depends(admin_user), db: DBSession = Depends(get_db)):
    limit = min(max(limit, 1), 500)
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    return [{"user_id": r.user_id, "action": r.action, "detail": r.detail, "created_at": r.created_at.isoformat()} for r in rows]
