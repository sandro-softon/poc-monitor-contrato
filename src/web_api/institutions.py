from datetime import date, datetime
from decimal import Decimal
from typing import Any

import mysql.connector
from mysql.connector import Error

from src.config import Config


ALLOWED_FIELDS = {
    "nome_instituicao": "NOME_INSTITUICAO",
    "numero_contrato": "NUM_CONTRATO",
    "dt_ini": "DT_INI",
    "dt_fim": "DT_FIM",
    "status": "STATUS",
    "produtos": "PRODUTOS",
    "tp_acessos": "TP_ACESSOS",
    "num_ac_contratados": "NUM_AC_CONTRATADOS",
    "numero_linhas_resultado": "NUMERO_LINHAS_RESULTADO",
}

SYNC_FIELDS = {
    "numero_contrato": "NUM_CONTRATO",
    "dt_ini": "DT_INI",
    "dt_fim": "DT_FIM",
}


def _json_value(value: Any):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, bytes):
        return int.from_bytes(value, "little")
    return value


class InstitutionRepository:
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

    def list_institutions(
        self, q: str | None = None, page: int = 1, page_size: int = 20
    ) -> dict:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        where = []
        params: list[Any] = []

        if q:
            like = f"%{q.strip()}%"
            where.append(
                "(CAST(COD_INSTITUICAO AS CHAR) LIKE %s "
                "OR NOME_INSTITUICAO LIKE %s "
                "OR NUM_CONTRATO LIKE %s)"
            )
            params.extend([like, like, like])

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        count_sql = f"SELECT COUNT(*) AS total FROM TB_INSTITUICAO {where_sql}"
        data_sql = f"""
            SELECT
                COD_INSTITUICAO AS codigo_instituicao,
                NOME_INSTITUICAO AS nome_instituicao,
                NUM_CONTRATO AS numero_contrato,
                DT_INI AS dt_ini,
                DT_FIM AS dt_fim,
                STATUS,
                PRODUTOS,
                TP_ACESSOS AS tp_acessos,
                NUM_AC_CONTRATADOS AS num_ac_contratados,
                NUMERO_LINHAS_RESULTADO AS numero_linhas_resultado
            FROM TB_INSTITUICAO
            {where_sql}
            ORDER BY NOME_INSTITUICAO
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
            raise RuntimeError(f"Erro ao consultar instituições: {e}") from e
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            if conn and conn.is_connected():
                conn.close()

    def get_institution(self, codigo: int) -> dict | None:
        query = """
            SELECT
                COD_INSTITUICAO AS codigo_instituicao,
                NOME_INSTITUICAO AS nome_instituicao,
                NUM_CONTRATO AS numero_contrato,
                DT_INI AS dt_ini,
                DT_FIM AS dt_fim,
                STATUS,
                PRODUTOS,
                TP_ACESSOS AS tp_acessos,
                NUM_AC_CONTRATADOS AS num_ac_contratados,
                NUMERO_LINHAS_RESULTADO AS numero_linhas_resultado
            FROM TB_INSTITUICAO
            WHERE COD_INSTITUICAO = %s
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, [codigo])
            row = cursor.fetchone()
            if not row:
                return None
            return {key: _json_value(value) for key, value in row.items()}
        except Error as e:
            raise RuntimeError(f"Erro ao consultar instituição: {e}") from e
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            if conn and conn.is_connected():
                conn.close()

    def update_institution(self, codigo: int, data: dict) -> dict:
        set_parts = []
        params: list[Any] = []

        for json_key, db_column in ALLOWED_FIELDS.items():
            if json_key in data:
                set_parts.append(f"{db_column} = %s")
                params.append(data[json_key])

        if set_parts:
            params.append(codigo)
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE TB_INSTITUICAO SET {', '.join(set_parts)} WHERE COD_INSTITUICAO = %s",
                    params,
                )
                conn.commit()
            except Error as e:
                raise RuntimeError(f"Erro ao atualizar instituição: {e}") from e
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
                if conn and conn.is_connected():
                    conn.close()

        self._sync_contrato(codigo, data)
        return self.get_institution(codigo)

    def _sync_contrato(self, codigo: int, data: dict):
        set_parts = []
        params: list[Any] = []
        for json_key, db_column in SYNC_FIELDS.items():
            if json_key in data:
                set_parts.append(f"{db_column} = %s")
                params.append(data[json_key])
        if not set_parts:
            return
        params.append(codigo)
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE TB_CONTRATO SET {', '.join(set_parts)} WHERE COD_INSTITUICAO = %s",
                params,
            )
            conn.commit()
        except Error:
            pass
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            if conn and conn.is_connected():
                conn.close()
