from datetime import datetime
import math

import pytest

from src.core.analyzer import ContractAnalyzer
from src.notifications.email_sender import (
    _format_brl,
    _format_limit,
    _format_number,
    _format_usage,
)
from src.readers.access_reader import AccessReader


class FakeContractReader:
    def __init__(self, service: str, shared_code=None, limit=1000, excess_value=None):
        self.service = service
        self.shared_code = shared_code
        self.limit = limit
        self.excess_value = excess_value

    def read_contracts(self):
        return [
            {
                "Codigo Instituicao": "123",
                "Cod Compartilhado": self.shared_code,
                "Nome Instituicao": "Cliente Teste",
                "Numero Contrato": "C-001",
                "Serviços Contratados": self.service,
                "data de corte início": datetime(2026, 1, 1),
                "data de corte final": datetime(2026, 12, 31),
                "acessos contratados": self.limit,
                "Frequencia": "Anual",
                "Valor Excedente": self.excess_value,
            }
        ]


class FakeAccessReader:
    def __init__(self):
        self.calls = []

    def get_accesses_by_service(self, codes, start_date, end_date):
        self.calls.append((codes, start_date, end_date))
        return {"API": 10, "Individual": 20, "Lote": 30}


@pytest.mark.parametrize(
    ("service", "expected_total", "expected_breakdown"),
    [
        ("API", 10, {"API": 10}),
        ("api", 10, {"API": 10}),
        ("Individual", 20, {"Individual": 20}),
        ("Lote", 30, {"Lote": 30}),
        ("Individual, API", 30, {"Individual": 20, "API": 10}),
        ("Individual, Lote, API", 60, {"Individual": 20, "Lote": 30, "API": 10}),
    ],
)
def test_access_total_sums_only_contracted_services(service, expected_total, expected_breakdown):
    access_reader = FakeAccessReader()
    analyzer = ContractAnalyzer(FakeContractReader(service), access_reader)

    alerts = analyzer.analyze(full=True)

    assert len(alerts) == 1
    assert alerts[0]["acessos_realizados"] == expected_total
    assert alerts[0]["acessos_breakdown"] == expected_breakdown


def test_unlimited_limit_is_preserved_and_does_not_calculate_usage():
    access_reader = FakeAccessReader()
    analyzer = ContractAnalyzer(FakeContractReader("Individual, API", limit="ILIMITADO"), access_reader)

    alerts = analyzer.analyze(full=True)

    assert alerts[0]["acessos_realizados"] == 30
    assert alerts[0]["limite_total"] is None
    assert alerts[0]["limite_ilimitado"] is True
    assert alerts[0]["perc_uso"] == 0.0


def test_test_filter_accepts_shared_code_and_passes_both_codes_to_access_reader():
    access_reader = FakeAccessReader()
    analyzer = ContractAnalyzer(
        FakeContractReader("API", shared_code="999"),
        access_reader,
    )

    alerts = analyzer.analyze(full=True, institution_code="999")

    assert len(alerts) == 1
    assert access_reader.calls[0][0] == ["123", "999"]


class FakeCursor:
    def __init__(self):
        self.params = None

    def execute(self, query, params):
        self.params = params

    def fetchall(self):
        return []

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()

    def cursor(self, dictionary=True):
        return self.cursor_instance

    def is_connected(self):
        return True

    def close(self):
        pass



def test_access_reader_uses_end_date_as_exclusive_limit(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(AccessReader, "get_connection", lambda self: connection)

    reader = AccessReader()
    reader.get_accesses_by_service(["123"], "2026-01-01 00:00:00", "2026-02-01 00:00:00")

    assert connection.cursor_instance.params == (
        "123", "2026-01-01", "2026-02-01",
        "123", "2026-01-01", "2026-02-01",
        "123", "2026-01-01", "2026-02-01",
    )


def test_email_formatters_for_unlimited_limit_and_nan_values():
    alert = {"limite_total": None, "limite_ilimitado": True, "perc_uso": 0.0}

    assert _format_limit(alert) == "∞"
    assert _format_usage(alert) == "-"
    assert _format_brl(math.nan) == "-"


def test_email_number_formatters_use_brazilian_separators():
    alert = {"limite_total": 180000, "limite_ilimitado": False, "perc_uso": 39.74}

    assert _format_number(71525) == "71.525"
    assert _format_number(1234567.89, 2) == "1.234.567,89"
    assert _format_limit(alert) == "180.000"
    assert _format_usage(alert) == "39,74%"
