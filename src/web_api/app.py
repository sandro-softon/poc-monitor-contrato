from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.web_api.auth import LoginRequest, LoginResponse, login, require_auth
from src.web_api.contracts import ContractRepository
from src.web_api.institutions import InstitutionRepository

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
def auth_login(data: LoginRequest, db: Session = Depends(get_db)):
    return login(data, db)


@app.get("/api/contracts", dependencies=[Depends(require_auth)])
def list_contracts(
    q: str | None = None,
    service: str | None = None,
    monitorar: int | None = Query(default=None, ge=0, le=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        return ContractRepository(db).list_contracts(
            q=q, service=service, monitorar=monitorar, page=page, page_size=page_size
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/contracts/{codigo}", dependencies=[Depends(require_auth)])
def get_contract_detail(
    codigo: int,
    db: Session = Depends(get_db),
):
    try:
        detail = ContractRepository(db).get_contract_detail(codigo)
        if detail is None:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")
        return detail
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.put("/api/contracts/{codigo}", dependencies=[Depends(require_auth)])
def update_contract(
    codigo: int,
    data: dict,
    db: Session = Depends(get_db),
):
    try:
        return ContractRepository(db).update_contract(codigo, data)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/institutions", dependencies=[Depends(require_auth)])
def list_institutions(
    q: str | None = None,
    status: int | None = Query(default=None, ge=0, le=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        return InstitutionRepository(db).list_institutions(
            q=q, status=status, page=page, page_size=page_size
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/institutions/{codigo}", dependencies=[Depends(require_auth)])
def get_institution(
    codigo: int,
    db: Session = Depends(get_db),
):
    try:
        inst = InstitutionRepository(db).get_institution(codigo)
        if inst is None:
            raise HTTPException(status_code=404, detail="Instituição não encontrada")
        return inst
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/contracts/{codigo}/services/{id_servico}", dependencies=[Depends(require_auth)])
def delete_service(
    codigo: int,
    id_servico: int,
    db: Session = Depends(get_db),
):
    try:
        result = ContractRepository(db).delete_service(codigo, id_servico)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/institutions", dependencies=[Depends(require_auth)])
def create_institution(
    data: dict,
    db: Session = Depends(get_db),
):
    try:
        return InstitutionRepository(db).create_institution(data)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.put("/api/institutions/{codigo}", dependencies=[Depends(require_auth)])
def update_institution(
    codigo: int,
    data: dict,
    db: Session = Depends(get_db),
):
    try:
        return InstitutionRepository(db).update_institution(codigo, data)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
