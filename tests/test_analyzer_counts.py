from datetime import datetime
import math

import pytest

from src.core.analyzer import ContractAnalyzer
from src.notifications.email_sender import (
    EmailSender,
    _format_brl,
    _format_limit,
    _format_number,
    _format_usage,
)
from src.readers.access_reader import AccessReader


class FakeContractReader:
    def __init__(
        self,
        service: str,
        shared_code=None,
        limit=1000,
        excess_value=None,
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 12, 31),
        frequency="Anual",
    ):
        self.service = service
        self.shared_code = shared_code
        self.limit = limit
        self.excess_value = excess_value
        self.start_date = start_date
        self.end_date = end_date
        self.frequency = frequency

    def read_contracts(self):
        return [
            {
                "Codigo Instituicao": "123",
                "Cod Compartilhado": self.shared_code,
                "Nome Instituicao": "Cliente Teste",
                "Numero Contrato": "C-001",
                "Serviços Contratados": self.service,
                "data de corte início": self.start_date,
                "data de corte final": self.end_date,
                "acessos contratados": self.limit,
                "Frequencia": self.frequency,
                "Valor Excedente": self.excess_value,
            }
        ]


class FakeAccessReader:
    def __init__(self):
        self.calls = []

    def get_accesses_by_service(self, codes, start_date, end_date):
        self.calls.append((codes, start_date, end_date))
        return {"API": 10, "Individual": 20, "Lote": 30}


class FixedDatetime(datetime):
    @classmethod
    def now(cls):
        return cls(2026, 6, 30, 12, 0, 0)


class FirstDayDatetime(datetime):
    @classmethod
    def now(cls):
        return cls(2026, 7, 1, 9, 40, 30)


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


def test_full_report_exposes_distinct_cutoff_dates(monkeypatch):
    monkeypatch.setattr("src.core.analyzer.datetime", FixedDatetime)
    access_reader = FakeAccessReader()
    analyzer = ContractAnalyzer(FakeContractReader("Individual, Lote"), access_reader)

    alerts = analyzer.analyze(full=True)

    assert alerts[0]["data_referencia_corte"] == "29/06/2026"
    assert alerts[0]["inicio_periodo_corte"] == "01/01/2026"
    assert alerts[0]["fim_periodo_corte"] == "29/06/2026"
    assert alerts[0]["fim_contrato"] == "31/12/2026"


def test_cycle_uses_consolidated_reference_on_first_day_of_month(monkeypatch):
    monkeypatch.setattr("src.core.analyzer.datetime", FirstDayDatetime)
    access_reader = FakeAccessReader()
    analyzer = ContractAnalyzer(
        FakeContractReader(
            "Individual, Lote",
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 5, 31),
            frequency="Mensal",
        ),
        access_reader,
    )

    alerts = analyzer.analyze(full=True)

    assert access_reader.calls[0][1:] == (
        "2026-06-01 00:00:00",
        "2026-07-01 00:00:00",
    )
    assert alerts[0]["data_referencia_corte"] == "30/06/2026"
    assert alerts[0]["inicio_periodo_corte"] == "01/06/2026"
    assert alerts[0]["fim_periodo_corte"] == "30/06/2026"


def test_full_report_email_lists_distinct_cutoff_dates(monkeypatch):
    sent = {}

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def starttls(self):
            pass

        def login(self, *args):
            pass

        def send_message(self, msg):
            sent["message"] = msg

    alert = {
        "instituicao": "Cliente Teste",
        "codigo": "123",
        "contrato": "C-001",
        "servico": "Individual, Lote",
        "motivos": ["Relatório Completo"],
        "data_referencia_corte": "29/06/2026",
        "inicio_periodo_corte": "01/06/2026",
        "fim_periodo_corte": "29/06/2026",
        "fim_contrato": "31/12/2026",
        "dias_restantes": 184,
        "frequencia": "Mensal",
        "acessos_breakdown": {"Individual": 20, "Lote": 30},
        "acessos_realizados": 50,
        "limite_total": 1000,
        "limite_ilimitado": False,
        "perc_uso": 5.0,
        "valor_excedente": None,
    }

    monkeypatch.setattr("smtplib.SMTP", DummySMTP)
    monkeypatch.setattr("smtplib.SMTP_SSL", DummySMTP)

    EmailSender().send_alert([alert], is_full_report=True)

    body = sent["message"].get_body(preferencelist=("plain",)).get_content()
    assert "Período de Corte.....: 01/06/2026 à 29/06/2026 (184 dias restantes)" in body
    assert "Data referência corte" not in body
    assert "Fim do Contrato" not in body


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
