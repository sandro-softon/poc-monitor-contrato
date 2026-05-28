from pathlib import Path
from src.readers.excel_reader import ContractReader


def test_read_softon_file():
    docs = Path(__file__).resolve().parents[1] / 'docs'
    file1 = docs / 'Softon_Controle de acessos_clientes_VF.xlsx'
    reader = ContractReader(str(file1))
    contracts = reader.read_contracts()
    assert isinstance(contracts, list)


def test_read_xsofton_file():
    docs = Path(__file__).resolve().parents[1] / 'docs'
    file2 = docs / 'xSofton_Controle de acessos_clientes_VF.xlsx'
    reader = ContractReader(str(file2))
    contracts = reader.read_contracts()
    assert isinstance(contracts, list)
