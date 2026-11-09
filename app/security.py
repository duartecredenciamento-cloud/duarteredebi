import hashlib, hmac, secrets
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException
from sqlalchemy import select
from .config import SESSION_HOURS, SESSION_SECRET
from .models import Session, User

COOKIE_NAME = "duarte_session"
def digits(value):
    return "".join(c for c in str(value or "") if c.isdigit())
def valid_cpf(value):
    cpf = digits(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        total = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        digit = (total * 10) % 11
        if digit == 10: digit = 0
        if digit != int(cpf[n]): return False
    return True
def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
    return f"pbkdf2_sha256$310000${salt.hex()}${key.hex()}"
def verify_password(password, encoded):
    try:
        scheme, rounds, salt, expected = encoded.split("$")
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return scheme == "pbkdf2_sha256" and hmac.compare_digest(actual, expected)
    except Exception:
        return False
def signed_token(raw):
    secret = (SESSION_SECRET or "development-only-change-before-deploy").encode()
    signature = hmac.new(secret, raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{signature}"
def create_session(db, user):
    raw = secrets.token_urlsafe(40)
    expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    db.add(Session(token_hash=hashlib.sha256(raw.encode()).hexdigest(), user_id=user.id, expires_at=expires))
    return raw, expires
def current_user(request: Request, db):
    cookie = request.cookies.get(COOKIE_NAME, "")
    raw, dot, signature = cookie.partition(".")
    if not dot or not hmac.compare_digest(signature, signed_token(raw).rsplit(".", 1)[1]):
        raise HTTPException(401, "Entre com seu CPF e senha.")
    row = db.scalar(select(Session).where(Session.token_hash == hashlib.sha256(raw.encode()).hexdigest()))
    if not row or row.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(401, "Sessão expirada. Entre novamente.")
    user = db.get(User, row.user_id)
    if not user or not user.active:
        raise HTTPException(401, "Acesso indisponível.")
    return user
def require_admin(user):
    if user.role != "admin":
        raise HTTPException(403, "Ação restrita ao Administrador Master.")
