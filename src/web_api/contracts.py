from sqlalchemy import cast, func, select, String, update
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


def _inst_to_dict(inst: Instituicao) -> dict:
    return {
        "codigo_instituicao": int(inst.codigo_instituicao),
        "nome_instituicao": inst.nome_instituicao,
        "numero_contrato": inst.numero_contrato,
        "dt_ini": inst.dt_ini.isoformat() if inst.dt_ini else None,
        "dt_fim": inst.dt_fim.isoformat() if inst.dt_fim else None,
        "cod_compartilhado": (
            int(inst.cod_compartilhado)
            if inst.cod_compartilhado is not None
            else None
        ),
        "dt_corte_inicial": (
            inst.dt_corte_inicial.isoformat() if inst.dt_corte_inicial else None
        ),
        "frequencia_corte": inst.frequencia_corte,
        "status": inst.status,
    }


def _servico_to_dict(s: Contrato) -> dict:
    return {
        "id": s.id_contrato,
        "servico": s.servicos_contratados,
        "num_ac_contratados": s.num_ac_contratados,
        "fl_acessos_ilimitados": bool(s.fl_acessos_ilimitados),
        "valor_excedente": (
            float(s.valor_excedente) if s.valor_excedente is not None else None
        ),
        "fl_monitorar_contrato": bool(s.fl_monitorar_contrato),
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

        base = select(Instituicao).join(
            Contrato,
            Contrato.codigo_instituicao == Instituicao.codigo_instituicao,
        )

        if q:
            like = f"%{q.strip()}%"
            base = base.where(
                cast(Instituicao.codigo_instituicao, String).like(like)
                | Instituicao.nome_instituicao.like(like)
                | Instituicao.numero_contrato.like(like)
            )

        if monitorar is not None:
            base = base.where(Contrato.fl_monitorar_contrato == monitorar)

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

        count_subq = (
            select(Instituicao.codigo_instituicao)
            .join(
                Contrato,
                Contrato.codigo_instituicao == Instituicao.codigo_instituicao,
            )
            .distinct()
        )
        if q:
            like = f"%{q.strip()}%"
            count_subq = count_subq.where(
                cast(Instituicao.codigo_instituicao, String).like(like)
                | Instituicao.nome_instituicao.like(like)
                | Instituicao.numero_contrato.like(like)
            )
        if monitorar is not None:
            count_subq = count_subq.where(
                Contrato.fl_monitorar_contrato == monitorar
            )
        nsvc = normalize_services(service or "")
        if nsvc:
            for item in nsvc.split(", "):
                count_subq = count_subq.where(
                    func.find_in_set(
                        item,
                        func.replace(
                            Contrato.servicos_contratados, ", ", ","
                        ),
                    )
                )

        total = self.db.scalar(
            select(func.count()).select_from(count_subq.subquery())
        )
        items = (
            self.db.scalars(
                base.order_by(Instituicao.nome_instituicao)
                .distinct()
                .offset(offset)
                .limit(page_size)
            )
            .all()
        )

        return {
            "items": [_inst_to_dict(inst) for inst in items],
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }

    def get_contract_detail(self, codigo: int) -> dict | None:
        inst = self.db.get(Instituicao, codigo)
        if not inst:
            return None

        servicos = (
            self.db.execute(
                select(Contrato)
                .where(Contrato.codigo_instituicao == codigo)
                .order_by(Contrato.servicos_contratados)
            )
            .scalars()
            .all()
        )

        result = _inst_to_dict(inst)
        result["servicos"] = [_servico_to_dict(s) for s in servicos]
        return result

    def update_contract(self, codigo: int, data: dict) -> dict:
        allowed_general = {
            "numero_contrato": "NUM_CONTRATO",
            "dt_ini": "DT_INI",
            "dt_fim": "DT_FIM",
            "cod_compartilhado": "COD_COMPARTILHADO",
            "dt_corte_inicial": "DT_CORTE_INICIAL",
            "frequencia_corte": "FREQUENCIA_CORTE",
            "status": "STATUS",
        }

        general_values = {
            db_col: data[json_key]
            for json_key, db_col in allowed_general.items()
            if json_key in data
        }
        if general_values:
            self.db.execute(
                update(Instituicao)
                .where(Instituicao.codigo_instituicao == codigo)
                .values(**general_values)
            )
            self.db.commit()

            sync_values = {
                db_col: data[json_key]
                for json_key, db_col in allowed_general.items()
                if json_key in data and db_col != "STATUS"
            }
            if sync_values:
                self.db.execute(
                    update(Contrato)
                    .where(Contrato.codigo_instituicao == codigo)
                    .values(**sync_values)
                )
                self.db.commit()

        if "servicos" in data and isinstance(data["servicos"], list):
            for svc_data in data["servicos"]:
                svc_id = svc_data.get("id")
                if not svc_id:
                    continue
                svc_values = {}
                for field in (
                    "servico",
                    "num_ac_contratados",
                    "fl_acessos_ilimitados",
                    "valor_excedente",
                    "fl_monitorar_contrato",
                ):
                    if field in svc_data:
                        svc_values[field] = svc_data[field]
                if svc_values:
                    self.db.execute(
                        update(Contrato)
                        .where(Contrato.id_contrato == svc_id)
                        .values(**svc_values)
                    )
                    self.db.commit()

        return self.get_contract_detail(codigo)
