from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from src.config import Config


security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def login(data: LoginRequest) -> LoginResponse:
    if data.username != Config.WEB_ADMIN_USER or data.password != Config.WEB_ADMIN_PASS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )
    return LoginResponse(access_token=Config.WEB_AUTH_TOKEN)


def require_auth(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if not credentials or credentials.credentials != Config.WEB_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação requerida",
        )
    return True
