from sqlalchemy import cast, func, select, String
from sqlalchemy.orm import Session

from src.db.models import Contrato, Instituicao

SERVICE_ORDER = ("Individual", "Lote", "API")
SERVICE_MAP = {
    "individual": "Individual",
    "lote": "Lote",
    "api": "API",
}


def normalize_services(value: str) -> str:
    services = set()
    for item in str(value or "").split(","):
        normalized = item.strip().lower()
        if normalized in SERVICE_MAP:
            services.add(SERVICE_MAP[normalized])
    return ", ".join(service for service in SERVICE_ORDER if service in services)


def _to_dict(row) -> dict:
    contrato, instituicao = row
    return {
        "id": contrato.id_contrato,
        "codigo_instituicao": int(contrato.codigo_instituicao),
        "nome_instituicao": instituicao.nome_instituicao,
        "numero_contrato": instituicao.numero_contrato,
        "servicos_contratados": contrato.servicos_contratados,
        "cod_compartilhado": (
            int(contrato.cod_compartilhado)
            if contrato.cod_compartilhado is not None
            else None
        ),
        "dt_ini": instituicao.dt_ini.isoformat() if instituicao.dt_ini else None,
        "dt_fim": instituicao.dt_fim.isoformat() if instituicao.dt_fim else None,
        "dt_corte_inicial": (
            contrato.dt_corte_inicial.isoformat()
            if contrato.dt_corte_inicial
            else None
        ),
        "frequencia_corte": contrato.frequencia_corte,
        "num_ac_contratados": contrato.num_ac_contratados,
        "fl_acessos_ilimitados": bool(contrato.fl_acessos_ilimitados),
        "valor_excedente": (
            float(contrato.valor_excedente)
            if contrato.valor_excedente is not None
            else None
        ),
        "fl_monitorar_contrato": bool(contrato.fl_monitorar_contrato),
    }


class ContractRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_contracts(
        self,
        q: str | None = None,
        service: str | None = None,
        monitorar: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        base = select(Contrato, Instituicao).join(
            Instituicao,
            Contrato.codigo_instituicao == Instituicao.codigo_instituicao,
        )

        if q:
            like = f"%{q.strip()}%"
            base = base.where(
                cast(Contrato.codigo_instituicao, String).like(like)
                | Instituicao.nome_instituicao.like(like)
                | Instituicao.numero_contrato.like(like)
            )

        normalized_service = normalize_services(service or "")
        if normalized_service:
            for item in normalized_service.split(", "):
                base = base.where(
                    func.find_in_set(
                        item,
                        func.replace(
                            Contrato.servicos_contratados, ", ", ","
                        ),
                    )
                )

        if monitorar is not None:
            base = base.where(Contrato.fl_monitorar_contrato == monitorar)

        total = self.db.scalar(
            select(func.count()).select_from(base.subquery())
        )

        rows = (
            self.db.execute(
                base.order_by(
                    Instituicao.nome_instituicao,
                    Instituicao.numero_contrato,
                    Contrato.servicos_contratados,
                )
                .offset(offset)
                .limit(page_size)
            )
            .all()
        )

        return {
            "items": [_to_dict(row) for row in rows],
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }
