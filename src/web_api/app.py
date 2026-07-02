from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.web_api.auth import LoginRequest, LoginResponse, login, require_auth
from src.web_api.contracts import ContractRepository


app = FastAPI(title="Monitor de Contratos API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=LoginResponse)
def auth_login(data: LoginRequest):
    return login(data)


@app.get("/api/contracts", dependencies=[Depends(require_auth)])
def list_contracts(
    q: str | None = None,
    service: str | None = None,
    monitorar: int | None = Query(default=None, ge=0, le=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    try:
        return ContractRepository().list_contracts(
            q=q,
            service=service,
            monitorar=monitorar,
            page=page,
            page_size=page_size,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
