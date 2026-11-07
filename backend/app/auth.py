import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# Contador de intentos fallidos por email para rate limiting
failed_login_attempts: dict[str, int] = {}
MAX_FAILED_ATTEMPTS = 5


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def _authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        # Usar hash falso para evitar ataques de tiempo (timing attack):
        # siempre ejecutar bcrypt.checkpw aunque el usuario no exista
        bcrypt.checkpw(password.encode(), bcrypt.hashpw(b"dummy", bcrypt.gensalt()))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    return user


def _cookie_domain() -> str | None:
    return settings.cookie_domain or None


def _cookie_secure(request: Request) -> bool:
    """Secure automático sobre HTTPS; puede forzarse con COOKIE_SECURE."""
    if settings.cookie_secure is not None:
        return settings.cookie_secure
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    return request.url.scheme == "https" or forwarded_proto.split(",")[0].strip().lower() == "https"


def _set_auth_cookies(response: Response, request: Request, access_token: str) -> None:
    max_age = settings.access_token_expire_minutes * 60
    common = {
        "max_age": max_age,
        "path": "/",
        "domain": _cookie_domain(),
        "secure": _cookie_secure(request),
        "samesite": settings.cookie_samesite,
    }
    # Token real: inaccesible para JavaScript (protege ante XSS).
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=access_token,
        httponly=True,
        **common,
    )
    # Marcador no sensible para que el frontend sepa si hay sesión sin leer el JWT.
    response.set_cookie(
        key=settings.session_marker_cookie,
        value="1",
        httponly=False,
        **common,
    )


def _clear_auth_cookies(response: Response, request: Request) -> None:
    for cookie_name in (settings.auth_cookie_name, settings.session_marker_cookie):
        response.delete_cookie(
            key=cookie_name,
            path="/",
            domain=_cookie_domain(),
            secure=_cookie_secure(request),
            samesite=settings.cookie_samesite,
        )


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = token or request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == subject).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    if body.password is None or len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres",
        )
    # Rate limiting: bloquear tras MAX_FAILED_ATTEMPTS intentos fallidos
    if failed_login_attempts.get(body.email, 0) >= MAX_FAILED_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Intente de nuevo más tarde.",
        )
    try:
        user = _authenticate(db, body.email, body.password)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            failed_login_attempts[body.email] = failed_login_attempts.get(body.email, 0) + 1
        raise
    # Éxito: resetear contador
    failed_login_attempts[body.email] = 0
    access_token = create_access_token(user.email)
    _set_auth_cookies(response, request, access_token)
    return TokenResponse(access_token=access_token)


@router.post("/token", response_model=TokenResponse)
def token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = _authenticate(db, form_data.username, form_data.password)
    access_token = create_access_token(user.email)
    _set_auth_cookies(response, request, access_token)
    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response) -> None:
    _clear_auth_cookies(response, request)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    return {"email": current_user.email}
