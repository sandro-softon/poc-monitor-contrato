import logging
from typing import Dict, List

import mysql.connector
from mysql.connector import Error

from src.config import Config


logger = logging.getLogger(__name__)


class ContractDbReader:
    def __init__(self):
        self.host = Config.DB_HOST
        self.user = Config.DB_USER
        self.password = Config.DB_PASS
        self.database = Config.DB_NAME

    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
            )
        except Error as e:
            logger.error("Erro ao conectar ao MySQL: %s", e)
            return None

    def read_contracts(self) -> List[Dict]:
        query = """
            SELECT
                c.COD_INSTITUICAO,
                i.NOME_INSTITUICAO,
                c.NUM_CONTRATO,
                c.SERVICOS_CONTRATADOS,
                c.COD_COMPARTILHADO,
                c.DT_CORTE_INICIAL,
                c.DT_FIM,
                c.FL_ACESSOS_ILIMITADOS,
                c.NUM_AC_CONTRATADOS,
                c.FREQUENCIA_CORTE,
                c.VALOR_EXCEDENTE
            FROM TB_CONTRATO c
            JOIN TB_INSTITUICAO i
              ON i.COD_INSTITUICAO = c.COD_INSTITUICAO
            WHERE c.FL_MONITORAR_CONTRATO = 1
            ORDER BY c.COD_INSTITUICAO, c.NUM_CONTRATO, c.SERVICOS_CONTRATADOS
        """

        conn = self.get_connection()
        if not conn:
            return []

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            rows = cursor.fetchall()
        except Error as e:
            logger.error("Erro ao consultar contratos no MySQL: %s", e)
            return []
        finally:
            if conn and conn.is_connected():
                if cursor:
                    cursor.close()
                conn.close()

        contracts = []
        for row in rows:
            unlimited = int(row.get("FL_ACESSOS_ILIMITADOS") or 0) == 1
            contracts.append(
                {
                    "Codigo Instituicao": str(row.get("COD_INSTITUICAO")),
                    "Nome Instituicao": row.get("NOME_INSTITUICAO"),
                    "Numero Contrato": row.get("NUM_CONTRATO") or "",
                    "Serviços Contratados": row.get("SERVICOS_CONTRATADOS"),
                    "Cod Compartilhado": ""
                    if row.get("COD_COMPARTILHADO") is None
                    else str(row.get("COD_COMPARTILHADO")),
                    "data de corte início": row.get("DT_CORTE_INICIAL"),
                    "data de corte final": row.get("DT_FIM"),
                    "acessos contratados": "ILIMITADO"
                    if unlimited
                    else row.get("NUM_AC_CONTRATADOS"),
                    "Frequencia": row.get("FREQUENCIA_CORTE"),
                    "Valor Excedente": row.get("VALOR_EXCEDENTE"),
                }
            )

        logger.info("Lidos %s contratos do banco de dados", len(contracts))
        return contracts
