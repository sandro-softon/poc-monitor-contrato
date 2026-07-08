from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock

from sqlalchemy import func, select

from src.db.models import Instituicao
from src.web_api.institutions import InstitutionRepository


def _make_inst(**overrides) -> MagicMock:
    inst = MagicMock(spec=Instituicao)
    defaults = {
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
    for key, value in {**defaults, **overrides}.items():
        setattr(inst, key, value)
    return inst


class FakeScalarResult:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items

    def first(self):
        return self.items[0] if self.items else None


def test_list_institutions_empty():
    db = MagicMock()
    db.scalar.return_value = 0
    db.scalars.return_value = FakeScalarResult([])

    repo = InstitutionRepository(db)
    result = repo.list_institutions()

    assert result["total"] == 0
    assert result["items"] == []
    assert result["page"] == 1


def test_list_institutions_with_search():
    mock_inst = _make_inst()

    db = MagicMock()
    db.scalar.return_value = 1
    db.scalars.return_value = FakeScalarResult([mock_inst])

    repo = InstitutionRepository(db)
    result = repo.list_institutions(q="teste")

    assert result["total"] == 1
    assert result["items"][0]["codigo_instituicao"] == 123
    assert result["items"][0]["nome_instituicao"] == "Cliente Teste"


def test_get_institution_found():
    mock_inst = _make_inst(
        codigo_instituicao=Decimal("456"),
        nome_instituicao="Cliente B",
        numero_contrato="C-002",
        tp_acessos="Lote",
        numero_linhas_resultado=Decimal("1000"),
    )

    db = MagicMock()
    db.get.return_value = mock_inst

    repo = InstitutionRepository(db)
    result = repo.get_institution(456)

    assert result["codigo_instituicao"] == 456
    assert result["nome_instituicao"] == "Cliente B"
    assert result["numero_linhas_resultado"] == 1000


def test_get_institution_not_found():
    db = MagicMock()
    db.get.return_value = None

    repo = InstitutionRepository(db)
    result = repo.get_institution(999)

    assert result is None


def test_update_institution_syncs_contrato():
    mock_inst = _make_inst(
        nome_instituicao="Cliente Atualizado",
        numero_contrato="C-NOVO",
        dt_fim=datetime(2027, 12, 31),
    )

    db = MagicMock()
    db.get.return_value = mock_inst

    repo = InstitutionRepository(db)
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
    assert db.commit.called
