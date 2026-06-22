import logging
import mysql.connector
from mysql.connector import Error
from typing import List, Dict
from datetime import datetime
from src.config import Config


logger = logging.getLogger(__name__)


class AccessReader:
    def __init__(self):
        self.host = Config.DB_HOST
        self.user = Config.DB_USER
        self.password = Config.DB_PASS
        self.database = Config.DB_NAME

    def get_connection(self):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            return conn
        except Error as e:
            logger.error("Erro ao conectar ao MySQL: %s", e)
            return None

    def get_accesses_by_service(
        self, codes: List[str], start_date: str, end_date: str
    ) -> Dict[str, int]:
        """
        Retorna o total de acessos por tipo de serviço (API, Individual, Lote)
        para uma lista de códigos de instituição e um período.

        - API: TB_LOG_ACESSOS_CONSOL onde COD_PRODUTO IS NOT NULL
        - Individual: TB_LOG_ACESSOS_CONSOL onde COD_PRODUTO IS NULL
        - Lote: TB_POWERMATCH_PROC somando QT_LINES

        Args:
            codes: Lista com 1 ou 2 códigos (Codigo Instituicao + Cod Compartilhado).
            start_date: Data início (descartando horas).
            end_date: Data fim exclusiva (descartando horas).

        Returns:
            Dicionário com chaves 'API', 'Individual', 'Lote' e seus totais.
        """
        # Abordagem: descartar horas/min/seg e usar o end_date como limite exclusivo.
        # Usa o operador >= inicio e < fim.
        try:
            dt_start = datetime.strptime(start_date[:10], "%Y-%m-%d")
            dt_end = datetime.strptime(end_date[:10], "%Y-%m-%d")

            start_param = dt_start.strftime("%Y-%m-%d")
            end_param = dt_end.strftime("%Y-%m-%d")
        except Exception:
            start_param = start_date[:10]
            end_param = end_date[:10]

        logger.debug(
            "[SQL PERÍODO] DATA_ACESSO/DT_CONCLUSAO >= %s e < %s | códigos=%s",
            start_param,
            end_param,
            ", ".join(codes),
        )

        result = {"API": 0, "Individual": 0, "Lote": 0}

        conn = self.get_connection()
        if not conn:
            return result

        # Constrói o placeholder IN para suportar 1 ou 2 códigos
        placeholders = ", ".join(["%s"] * len(codes))

        query = f"""
            SELECT 'API' AS tipo, COALESCE(SUM(QT_ACESSOS), 0) AS total
            FROM TB_LOG_ACESSOS_CONSOL
            WHERE COD_CONTA IN ({placeholders})
              AND DATA_ACESSO >= %s AND DATA_ACESSO < %s
              AND COD_PRODUTO IS NOT NULL

            UNION ALL

            SELECT 'Individual' AS tipo, COALESCE(SUM(QT_ACESSOS), 0) AS total
            FROM TB_LOG_ACESSOS_CONSOL
            WHERE COD_CONTA IN ({placeholders})
              AND DATA_ACESSO >= %s AND DATA_ACESSO < %s
              AND COD_PRODUTO IS NULL

            UNION ALL

            SELECT 'Lote' AS tipo, COALESCE(SUM(QT_LINES), 0) AS total
            FROM TB_POWERMATCH_PROC
            WHERE COD_INSTITUICAO IN ({placeholders})
              AND DT_CONCLUSAO IS NOT NULL
              AND DT_CONCLUSAO >= %s AND DT_CONCLUSAO < %s
        """

        # Parâmetros: cada bloco precisa dos codes + datas
        params = (
            *codes, start_param, end_param,   # API
            *codes, start_param, end_param,   # Individual
            *codes, start_param, end_param,   # Lote
        )

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                tipo = row["tipo"]
                if tipo in result:
                    result[tipo] = int(row["total"])
        except Error as e:
            logger.error("Erro na consulta de acessos para %s: %s", codes, e)
        finally:
            if conn and conn.is_connected():
                if cursor:
                    cursor.close()
                conn.close()

        return result
