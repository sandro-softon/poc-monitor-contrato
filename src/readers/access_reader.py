import mysql.connector
from mysql.connector import Error
from typing import List, Dict
from datetime import datetime, timedelta
from src.config import Config


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
            print(f"Erro ao conectar ao MySQL: {e}")
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
            end_date: Data fim (descartando horas, somando 1 dia para limite exclusivo).

        Returns:
            Dicionário com chaves 'API', 'Individual', 'Lote' e seus totais.
        """
        # Abordagem: descartar horas/min/seg e somar 1 dia no end_date
        # Usa o operador >= inicio e < proximo_dia_fim
        try:
            dt_start = datetime.strptime(start_date[:10], "%Y-%m-%d")
            dt_end = datetime.strptime(end_date[:10], "%Y-%m-%d") + timedelta(days=1)
            
            start_param = dt_start.strftime("%Y-%m-%d")
            end_param = dt_end.strftime("%Y-%m-%d")
        except Exception:
            start_param = start_date[:10]
            end_param = end_date[:10]

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

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                tipo = row["tipo"]
                if tipo in result:
                    result[tipo] = int(row["total"])
        except Error as e:
            print(f"Erro na consulta de acessos para {codes}: {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

        return result
