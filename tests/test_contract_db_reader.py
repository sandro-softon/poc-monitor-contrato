from datetime import datetime
from decimal import Decimal

import mysql.connector

from src.readers.contract_db_reader import ContractDbReader


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.query = None

    def execute(self, query):
        self.query = query

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)

    def cursor(self, dictionary=True):
        return self.cursor_instance

    def is_connected(self):
        return True

    def close(self):
        pass


def test_contract_db_reader_maps_database_rows(monkeypatch):
    rows = [
        {
            "COD_INSTITUICAO": Decimal("123"),
            "NOME_INSTITUICAO": "Cliente Teste",
            "NUM_CONTRATO": "C-001",
            "SERVICOS_CONTRATADOS": "Individual, API",
            "COD_COMPARTILHADO": Decimal("999"),
            "DT_CORTE_INICIAL": datetime(2026, 1, 1),
            "DT_FIM": datetime(2026, 12, 31),
            "FL_ACESSOS_ILIMITADOS": 1,
            "NUM_AC_CONTRATADOS": None,
            "FREQUENCIA_CORTE": "Mensal",
            "VALOR_EXCEDENTE": Decimal("1.25"),
        }
    ]
    connection = FakeConnection(rows)
    monkeypatch.setattr(mysql.connector, "connect", lambda **kwargs: connection)

    contracts = ContractDbReader().read_contracts()

    assert contracts == [
        {
            "Codigo Instituicao": "123",
            "Nome Instituicao": "Cliente Teste",
            "Numero Contrato": "C-001",
            "Serviços Contratados": "Individual, API",
            "Cod Compartilhado": "999",
            "data de corte início": datetime(2026, 1, 1),
            "data de corte final": datetime(2026, 12, 31),
            "acessos contratados": "ILIMITADO",
            "Frequencia": "Mensal",
            "Valor Excedente": Decimal("1.25"),
        }
    ]
    assert "FROM TB_CONTRATO c" in connection.cursor_instance.query
    assert "i.NUM_CONTRATO" in connection.cursor_instance.query
    assert "i.DT_FIM" in connection.cursor_instance.query
