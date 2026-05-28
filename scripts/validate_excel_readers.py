#!/usr/bin/env python3
from pathlib import Path
from src.readers.excel_reader import ContractReader
import logging

logging.basicConfig(level=logging.INFO)


def validate(path: Path):
    print(f"\nValidating: {path}")
    reader = ContractReader(str(path))
    contracts = reader.read_contracts()
    print(f"  Contracts read: {len(contracts)}")
    if contracts:
        sample = contracts[0]
        keys = list(sample.keys())
        print(f"  Sample keys: {keys}")
        # print first 3 institution names
        nomes = [c.get('Nome Instituicao') for c in contracts[:3]]
        print(f"  Sample names: {nomes}")


def main():
    docs = Path(__file__).resolve().parents[1] / 'docs'
    candidates = [
        docs / 'Softon_Controle de acessos_clientes_VF.xlsx',
        docs / 'xSofton_Controle de acessos_clientes_VF.xlsx',
    ]
    for c in candidates:
        if c.exists():
            validate(c)
        else:
            print(f"File not found: {c}")


if __name__ == '__main__':
    main()
