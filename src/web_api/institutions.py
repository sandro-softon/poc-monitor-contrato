from sqlalchemy import cast, func, select, String, update
from sqlalchemy.orm import Session

from src.db.models import Contrato, Instituicao

ALLOWED_FIELDS = {
    "nome_instituicao": "NOME_INSTITUICAO",
    "numero_contrato": "NUM_CONTRATO",
    "dt_ini": "DT_INI",
    "dt_fim": "DT_FIM",
    "cod_compartilhado": "COD_COMPARTILHADO",
    "dt_corte_inicial": "DT_CORTE_INICIAL",
    "frequencia_corte": "FREQUENCIA_CORTE",
    "status": "STATUS",
    "num_ac_contratados": "NUM_AC_CONTRATADOS",
    "numero_linhas_resultado": "NUMERO_LINHAS_RESULTADO",
}

SYNC_FIELDS = {
    "numero_contrato": "NUM_CONTRATO",
    "dt_ini": "DT_INI",
    "dt_fim": "DT_FIM",
    "cod_compartilhado": "COD_COMPARTILHADO",
    "dt_corte_inicial": "DT_CORTE_INICIAL",
    "frequencia_corte": "FREQUENCIA_CORTE",
}


def _to_dict(inst: Instituicao) -> dict:
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
        "num_ac_contratados": inst.num_ac_contratados,
        "numero_linhas_resultado": (
            int(inst.numero_linhas_resultado)
            if inst.numero_linhas_resultado is not None
            else None
        ),
    }


class InstitutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_institutions(
        self,
        q: str | None = None,
        status: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        base = select(Instituicao)

        if q:
            like = f"%{q.strip()}%"
            base = base.where(
                cast(Instituicao.codigo_instituicao, String).like(like)
                | Instituicao.nome_instituicao.like(like)
                | Instituicao.numero_contrato.like(like)
            )

        if status is not None:
            base = base.where(Instituicao.status == status)

        total = self.db.scalar(select(func.count()).select_from(base.subquery()))
        items = (
            self.db.scalars(
                base.order_by(Instituicao.nome_instituicao)
                .offset(offset)
                .limit(page_size)
            )
            .all()
        )

        return {
            "items": [_to_dict(inst) for inst in items],
            "total": total or 0,
            "page": page,
            "page_size": page_size,
        }

    def get_institution(self, codigo: int) -> dict | None:
        inst = self.db.get(Instituicao, codigo)
        if not inst:
            return None
        return _to_dict(inst)

    def create_institution(self, data: dict) -> dict:
        codigo = data.get("codigo_instituicao")
        if not codigo:
            raise RuntimeError("codigo_instituicao é obrigatório")
        nome = data.get("nome_instituicao")
        if not nome:
            raise RuntimeError("nome_instituicao é obrigatório")

        from sqlalchemy import insert

        inst_values = {
            "COD_INSTITUICAO": codigo,
            "NOME_INSTITUICAO": nome,
            "NUM_CONTRATO": data.get("numero_contrato"),
            "DT_INI": data.get("dt_ini"),
            "DT_FIM": data.get("dt_fim"),
            "COD_COMPARTILHADO": data.get("cod_compartilhado"),
            "DT_CORTE_INICIAL": data.get("dt_corte_inicial"),
            "FREQUENCIA_CORTE": data.get("frequencia_corte"),
            "NUM_AC_CONTRATADOS": data.get("num_ac_contratados"),
            "TP_ACESSOS": data.get("tp_acessos", "Individual"),
            "PRODUTOS": data.get("produtos", "flex,gov"),
            "STATUS": data.get("status", 1),
            "NUMERO_LINHAS_RESULTADO": data.get("numero_linhas_resultado"),
            "QT_MONITORAMENTO": 0,
            "FL_PESQUISA_INDIVUDUAL": 1,
            "FL_DADOS_COMPLEMENTARES": 0,
            "FL_POWER_MATCH": b'\x00',
            "TXT_VALID_IP": "*",
        }
        inst_values = {k: v for k, v in inst_values.items() if v is not None}
        self.db.execute(insert(Instituicao.__table__).values(**inst_values))
        self.db.commit()

        servicos = data.get("servicos", [])
        for svc in servicos:
            servico = svc.get("servico", "")
            if not servico:
                continue
            self.db.execute(
                insert(Contrato.__table__).values(
                    COD_INSTITUICAO=codigo,
                    NUM_CONTRATO=data.get("numero_contrato"),
                    DT_INI=data.get("dt_ini"),
                    DT_FIM=data.get("dt_fim"),
                    COD_COMPARTILHADO=data.get("cod_compartilhado"),
                    DT_CORTE_INICIAL=data.get("dt_corte_inicial"),
                    FREQUENCIA_CORTE=data.get("frequencia_corte"),
                    SERVICOS_CONTRATADOS=servico,
                    NUM_AC_CONTRATADOS=svc.get("num_ac_contratados"),
                    FL_ACESSOS_ILIMITADOS=svc.get("fl_acessos_ilimitados", 0),
                    VALOR_EXCEDENTE=svc.get("valor_excedente"),
                    FL_MONITORAR_CONTRATO=1,
                )
            )
        self.db.commit()

        return self.get_institution(codigo)

    def update_institution(self, codigo: int, data: dict) -> dict:
        values = {
            db_col: data[json_key]
            for json_key, db_col in ALLOWED_FIELDS.items()
            if json_key in data
        }
        if values:
            self.db.execute(
                update(Instituicao)
                .where(Instituicao.codigo_instituicao == codigo)
                .values(**values)
                .execution_options(synchronize_session=False)
            )
            self.db.commit()

        self._sync_contrato(codigo, data)
        return self.get_institution(codigo)

    def _sync_contrato(self, codigo: int, data: dict):
        values = {
            db_col: data[json_key]
            for json_key, db_col in SYNC_FIELDS.items()
            if json_key in data
        }
        if values:
            self.db.execute(
                update(Contrato)
                .where(Contrato.codigo_instituicao == codigo)
                .values(**values)
                .execution_options(synchronize_session=False)
            )
            self.db.commit()
