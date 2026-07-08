from datetime import datetime
from decimal import Decimal

import mysql.connector

from src.web_api.institutions import InstitutionRepository


class FakeCursor:
    def __init__(self, count_total=0, data_rows=None):
        self.data_rows = data_rows or []
        self.count_total = count_total
        self.queries: list[str] = []
        self._is_count = True

    def execute(self, query, params=None):
        self.queries.append(query)
        self._is_count = "COUNT(*)" in query.upper()

    def fetchone(self):
        if self._is_count:
            return {"total": self.count_total}
        return self.data_rows[0] if self.data_rows else None

    def fetchall(self):
        return self.data_rows

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.committed = False

    def cursor(self, dictionary=True):
        return FakeCursor()

    def is_connected(self):
        return True

    def commit(self):
        self.committed = True

    def close(self):
        pass


def test_list_institutions_empty(monkeypatch):
    conn = FakeConnection()
    c = FakeCursor(count_total=0, data_rows=[])
    conn.cursor = lambda dictionary=True: c
    monkeypatch.setattr(mysql.connector, "connect", lambda **kwargs: conn)

    repo = InstitutionRepository()
    result = repo.list_institutions()

    assert result["total"] == 0
    assert result["items"] == []
    assert result["page"] == 1


def test_list_institutions_with_search(monkeypatch):
    conn = FakeConnection()
    c = FakeCursor(
        count_total=1,
        data_rows=[
            {
                "codigo_instituicao": Decimal("123"),
                "nome_instituicao": "Cliente Teste",
                "numero_contrato": "C-001",
                "dt_ini": datetime(2026, 1, 1),
                "dt_fim": datetime(2026, 12, 31),
                "status": 1,
                "produtos": "flex,gov",
                "tp_acessos": "Individual, Lote",
                "num_ac_contratados": Decimal("50000"),
                "numero_linhas_resultado": None,
            }
        ],
    )
    conn.cursor = lambda dictionary=True: c
    monkeypatch.setattr(mysql.connector, "connect", lambda **kwargs: conn)

    repo = InstitutionRepository()
    result = repo.list_institutions(q="teste")

    assert result["total"] == 1
    assert result["items"][0]["codigo_instituicao"] == 123
    assert result["items"][0]["nome_instituicao"] == "Cliente Teste"

    query_upper = c.queries[0].upper()
    assert "LIKE" in query_upper


def test_get_institution_found(monkeypatch):
    conn = FakeConnection()
    c = FakeCursor(
        data_rows=[
            {
                "codigo_instituicao": Decimal("456"),
                "nome_instituicao": "Cliente B",
                "numero_contrato": "C-002",
                "dt_ini": datetime(2026, 2, 1),
                "dt_fim": datetime(2026, 2, 28),
                "status": 1,
                "produtos": "flex",
                "tp_acessos": "Lote",
                "num_ac_contratados": None,
                "numero_linhas_resultado": Decimal("1000"),
            }
        ]
    )
    conn.cursor = lambda dictionary=True: c
    monkeypatch.setattr(mysql.connector, "connect", lambda **kwargs: conn)

    repo = InstitutionRepository()
    result = repo.get_institution(456)

    assert result["codigo_instituicao"] == 456
    assert result["nome_instituicao"] == "Cliente B"
    assert result["numero_linhas_resultado"] == 1000
    assert "COD_INSTITUICAO = %s" in c.queries[0]


def test_get_institution_not_found(monkeypatch):
    conn = FakeConnection()
    c = FakeCursor(data_rows=[])
    conn.cursor = lambda dictionary=True: c
    monkeypatch.setattr(mysql.connector, "connect", lambda **kwargs: conn)

    repo = InstitutionRepository()
    result = repo.get_institution(999)
    assert result is None


def test_update_institution_syncs_contrato(monkeypatch):
    sql_updates: list[tuple[str, list]] = []
    select_called = False

    class TrackingCursor:
        def __init__(self, dictionary=False):
            self.dictionary = dictionary
            self.query = None

        def execute(self, query, params=None):
            nonlocal select_called
            self.query = query
            if query.strip().upper().startswith("UPDATE"):
                sql_updates.append((query, params or []))
            elif "WHERE COD_INSTITUICAO = %s" in query and "SELECT" in query:
                select_called = True

        def fetchone(self):
            return {
                "codigo_instituicao": Decimal("123"),
                "nome_instituicao": "Cliente Atualizado",
                "numero_contrato": "C-NOVO",
                "dt_ini": datetime(2026, 1, 1),
                "dt_fim": datetime(2027, 12, 31),
                "status": 1,
                "produtos": "flex,gov",
                "tp_acessos": "Individual",
                "num_ac_contratados": Decimal("100000"),
                "numero_linhas_resultado": None,
            }

        def fetchall(self):
            return [self.fetchone()]

        def close(self):
            pass

    class TrackingConnection:
        def __init__(self):
            self.committed = False

        def cursor(self, dictionary=True):
            return TrackingCursor(dictionary=dictionary)

        def is_connected(self):
            return True

        def commit(self):
            self.committed = True

        def close(self):
            pass

    conn = TrackingConnection()
    monkeypatch.setattr(mysql.connector, "connect", lambda **kwargs: conn)

    repo = InstitutionRepository()
    result = repo.update_institution(
        123,
        {
            "nome_instituicao": "Cliente Atualizado",
            "numero_contrato": "C-NOVO",
            "dt_fim": datetime(2027, 12, 31),
        },
    )

    assert result["codigo_instituicao"] == 123
    assert result["nome_instituicao"] == "Cliente Atualizado"
    assert conn.committed

    update_queries = [q for q, _ in sql_updates if "UPDATE" in q]
    assert len(update_queries) >= 2
    assert any("TB_CONTRATO" in q for q in update_queries)
    assert any("TB_INSTITUICAO" in q for q in update_queries)
