from sqlalchemy import cast, delete as sa_delete, func, insert, select, String, text, update
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


def _inst_to_dict(inst: Instituicao, servicos: list[str] | None = None) -> dict:
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
        "servicos": servicos or [],
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
        monitorar: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        codes_where = []
        params: dict = {}

        if q:
            like = f"%{q.strip()}%"
            codes_where.append(
                "(CAST(i.COD_INSTITUICAO AS CHAR) LIKE :q1 "
                "OR i.NOME_INSTITUICAO LIKE :q2 "
                "OR i.NUM_CONTRATO LIKE :q3)"
            )
            params["q1"] = like
            params["q2"] = like
            params["q3"] = like

        if monitorar is not None:
            codes_where.append("c.FL_MONITORAR_CONTRATO = :mon")
            params["mon"] = monitorar

        where_sql = f"WHERE {' AND '.join(codes_where)}" if codes_where else ""

        count_sql = f"""
            SELECT COUNT(DISTINCT i.COD_INSTITUICAO)
            FROM TB_INSTITUICAO i
            JOIN TB_CONTRATO c ON c.COD_INSTITUICAO = i.COD_INSTITUICAO
            {where_sql}
        """
        total = self.db.execute(text(count_sql), params).scalar()

        data_sql = f"""
            SELECT
                i.COD_INSTITUICAO,
                GROUP_CONCAT(c.SERVICOS_CONTRATADOS
                    ORDER BY c.SERVICOS_CONTRATADOS SEPARATOR ', '
                ) AS SERVICOS
            FROM TB_INSTITUICAO i
            JOIN TB_CONTRATO c ON c.COD_INSTITUICAO = i.COD_INSTITUICAO
            {where_sql}
            GROUP BY i.COD_INSTITUICAO
            ORDER BY i.NOME_INSTITUICAO
            LIMIT :lim OFFSET :off
        """
        params["lim"] = page_size
        params["off"] = offset
        rows = self.db.execute(text(data_sql), params).fetchall()
        servicos_map = {row[0]: row[1] for row in rows}

        inst_codes = list(servicos_map.keys())
        if not inst_codes:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

        insts = self.db.scalars(
            select(Instituicao)
            .where(Instituicao.codigo_instituicao.in_(inst_codes))
            .order_by(Instituicao.nome_instituicao)
        ).all()

        return {
            "items": [
                _inst_to_dict(
                    inst,
                    servicos=servicos_map.get(int(inst.codigo_instituicao), "").split(", "),
                )
                for inst in insts
            ],
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
        dt_ini = data.get("dt_ini")
        dt_fim = data.get("dt_fim")
        if dt_ini and dt_fim and dt_fim <= dt_ini:
            raise RuntimeError("Data Fim deve ser maior que Data Início")
        allowed_general = {
            "numero_contrato": "NUM_CONTRATO",
            "dt_ini": "DT_INI",
            "dt_fim": "DT_FIM",
            "cod_compartilhado": "COD_COMPARTILHADO",
            "dt_corte_inicial": "DT_CORTE_INICIAL",
            "frequencia_corte": "FREQUENCIA_CORTE",
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
                .execution_options(synchronize_session=False)
            )
            self.db.commit()

            sync_values = {
                db_col: data[json_key]
                for json_key, db_col in allowed_general.items()
                if json_key in data
            }
            if sync_values:
                self.db.execute(
                    update(Contrato)
                    .where(Contrato.codigo_instituicao == codigo)
                    .values(**sync_values)
                    .execution_options(synchronize_session=False)
                )
                self.db.commit()

        if "servicos" in data and isinstance(data["servicos"], list):
            incoming_ids = set()
            for svc_data in data["servicos"]:
                svc_id = svc_data.get("id")
                if svc_id and svc_id > 0:
                    incoming_ids.add(svc_id)
                    db_col_map = {
                        "servico": "SERVICOS_CONTRATADOS",
                        "num_ac_contratados": "NUM_AC_CONTRATADOS",
                        "fl_acessos_ilimitados": "FL_ACESSOS_ILIMITADOS",
                        "valor_excedente": "VALOR_EXCEDENTE",
                    }
                    svc_values = {}
                    for json_key, db_col in db_col_map.items():
                        if json_key in svc_data:
                            svc_values[db_col] = svc_data[json_key]
                    if svc_values:
                        self.db.execute(
                            update(Contrato)
                            .where(Contrato.id_contrato == svc_id)
                            .values(**svc_values)
                            .execution_options(synchronize_session=False)
                        )
                        self.db.commit()
                elif svc_id is None or svc_id == 0:
                    servico = svc_data.get("servico", "")
                    if not servico:
                        continue
                    inst = self.db.get(Instituicao, codigo)
                    insert_values = {
                        "COD_INSTITUICAO": codigo,
                        "NUM_CONTRATO": inst.numero_contrato if inst else None,
                        "DT_INI": inst.dt_ini if inst else None,
                        "DT_FIM": inst.dt_fim if inst else None,
                        "COD_COMPARTILHADO": inst.cod_compartilhado if inst else None,
                        "DT_CORTE_INICIAL": inst.dt_corte_inicial if inst else None,
                        "FREQUENCIA_CORTE": inst.frequencia_corte if inst else None,
                        "SERVICOS_CONTRATADOS": servico,
                        "NUM_AC_CONTRATADOS": svc_data.get("num_ac_contratados"),
                        "FL_ACESSOS_ILIMITADOS": svc_data.get("fl_acessos_ilimitados", 0),
                        "VALOR_EXCEDENTE": svc_data.get("valor_excedente"),
                        "FL_MONITORAR_CONTRATO": svc_data.get("fl_monitorar_contrato", 1),
                    }
                    self.db.execute(insert(Contrato).values(**insert_values))
                    self.db.commit()

            existing_ids = set(
                self.db.execute(
                    select(Contrato.id_contrato).where(
                        Contrato.codigo_instituicao == codigo
                    )
                )
                .scalars()
                .all()
            )
            to_delete = existing_ids - incoming_ids
            if to_delete:
                self.db.execute(
                    sa_delete(Contrato).where(Contrato.id_contrato.in_(to_delete))
                )
                self.db.commit()

        return self.get_contract_detail(codigo)

    def delete_service(self, codigo_instituicao: int, id_servico: int) -> dict:
        svc = self.db.get(Contrato, id_servico)
        if not svc or svc.codigo_instituicao != codigo_instituicao:
            return {"error": "Serviço não encontrado"}
        self.db.execute(
            update(Contrato)
            .where(Contrato.id_contrato == id_servico)
            .values(fl_monitorar_contrato=0, num_ac_contratados=None, valor_excedente=None)
        )
        self.db.commit()
        return self.get_contract_detail(codigo_instituicao)
