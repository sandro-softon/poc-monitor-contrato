from datetime import date, datetime
from decimal import Decimal
from typing import Any

import mysql.connector
from mysql.connector import Error

from src.config import Config


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


def _json_value(value: Any):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


class ContractRepository:
    def __init__(self):
        self.host = Config.DB_HOST
        self.user = Config.DB_USER
        self.password = Config.DB_PASS
        self.database = Config.DB_NAME

    def get_connection(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
        )

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

        where = []
        params: list[Any] = []

        if q:
            like = f"%{q.strip()}%"
            where.append(
                "(CAST(c.COD_INSTITUICAO AS CHAR) LIKE %s "
                "OR i.NOME_INSTITUICAO LIKE %s "
                "OR i.NUM_CONTRATO LIKE %s)"
            )
            params.extend([like, like, like])

        normalized_service = normalize_services(service or "")
        if normalized_service:
            for item in normalized_service.split(", "):
                where.append("FIND_IN_SET(%s, REPLACE(c.SERVICOS_CONTRATADOS, ', ', ','))")
                params.append(item)

        if monitorar is not None:
            where.append("c.FL_MONITORAR_CONTRATO = %s")
            params.append(monitorar)

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM TB_CONTRATO c
            JOIN TB_INSTITUICAO i
              ON i.COD_INSTITUICAO = c.COD_INSTITUICAO
            {where_sql}
        """
        data_sql = f"""
            SELECT
                c.ID_CONTRATO AS id,
                c.COD_INSTITUICAO AS codigo_instituicao,
                i.NOME_INSTITUICAO AS nome_instituicao,
                i.NUM_CONTRATO AS numero_contrato,
                c.SERVICOS_CONTRATADOS AS servicos_contratados,
                c.COD_COMPARTILHADO AS cod_compartilhado,
                i.DT_INI AS dt_ini,
                i.DT_FIM AS dt_fim,
                c.DT_CORTE_INICIAL AS dt_corte_inicial,
                c.FREQUENCIA_CORTE AS frequencia_corte,
                c.NUM_AC_CONTRATADOS AS num_ac_contratados,
                c.FL_ACESSOS_ILIMITADOS AS fl_acessos_ilimitados,
                c.VALOR_EXCEDENTE AS valor_excedente,
                c.FL_MONITORAR_CONTRATO AS fl_monitorar_contrato
            FROM TB_CONTRATO c
            JOIN TB_INSTITUICAO i
              ON i.COD_INSTITUICAO = c.COD_INSTITUICAO
            {where_sql}
            ORDER BY i.NOME_INSTITUICAO, i.NUM_CONTRATO, c.SERVICOS_CONTRATADOS
            LIMIT %s OFFSET %s
        """

        conn = self.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(count_sql, params)
            total = int(cursor.fetchone()["total"])
            cursor.execute(data_sql, [*params, page_size, offset])
            items = [
                {key: _json_value(value) for key, value in row.items()}
                for row in cursor.fetchall()
            ]
            return {"items": items, "total": total, "page": page, "page_size": page_size}
        except Error as e:
            raise RuntimeError(f"Erro ao consultar contratos: {e}") from e
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            if conn and conn.is_connected():
                conn.close()
