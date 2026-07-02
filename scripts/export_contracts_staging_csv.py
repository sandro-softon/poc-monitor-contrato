import argparse
import csv
import math
import sys
import unicodedata
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config


OUTPUT_COLUMNS = [
    "COD_INSTITUICAO",
    "COD_COMPARTILHADO",
    "NOME_INSTITUICAO",
    "NUM_CONTRATO",
    "DT_CORTE_INICIAL",
    "FREQUENCIA_CORTE",
    "SERVICOS_CONTRATADOS",
    "NUM_AC_CONTRATADOS",
    "VALOR_EXCEDENTE",
    "FL_MONITORAR_CONTRATO",
]

SERVICE_ORDER = ("Individual", "Lote", "API")
SERVICE_MAP = {
    "individual": "Individual",
    "lote": "Lote",
    "api": "API",
}


def _normalize_name(value: object) -> str:
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFKD", value.strip().lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.replace(" ", "").replace("_", "")


def _find_column(columns: list[str], keywords: list[str]) -> str | None:
    for column in columns:
        normalized = _normalize_name(column)
        if all(keyword in normalized for keyword in keywords):
            return column
    return None


def _is_missing(value: object) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value)


def _code(value: object) -> str:
    if _is_missing(value):
        return ""
    text = str(value).strip()
    if text in {"-", "--"}:
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    if not text.isdigit():
        return ""
    return text


def _text(value: object) -> str:
    if _is_missing(value):
        return ""
    return str(value).strip()


def _services(value: object) -> str:
    services = set()
    for item in _text(value).split(","):
        normalized = _normalize_name(item)
        if normalized in SERVICE_MAP:
            services.add(SERVICE_MAP[normalized])
    return ", ".join(service for service in SERVICE_ORDER if service in services)


def _date(value: object) -> str:
    if _is_missing(value):
        return ""
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return ""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def _select_sheet(excel_path: str, sheet_name: str | None) -> pd.DataFrame:
    if sheet_name:
        return pd.read_excel(excel_path, sheet_name=sheet_name)

    sheets = pd.read_excel(excel_path, sheet_name=None)
    for df in sheets.values():
        joined = " ".join(_normalize_name(column) for column in df.columns)
        if all(keyword in joined for keyword in ("codigo", "institu", "acesso")):
            return df
    return next(iter(sheets.values()))


def _build_mapping(columns: list[str]) -> dict[str, str | None]:
    return {
        "codigo": _find_column(columns, ["codigo", "instituicao"])
        or _find_column(columns, ["cod", "instituicao"]),
        "cod_compartilhado": _find_column(columns, ["cod", "compartilhado"]),
        "nome": _find_column(columns, ["nome", "instituicao"]),
        "servicos": _find_column(columns, ["servicos", "contratados"]),
        "numero_contrato": _find_column(columns, ["numero", "contrato"]),
        "valor_excedente": _find_column(columns, ["valor", "excedente"]),
        "data_inicio": _find_column(columns, ["data", "corte", "inicio"])
        or _find_column(columns, ["inicio"]),
        "frequencia": _find_column(columns, ["frequencia"]),
        "acessos": _find_column(columns, ["acessos", "contratados"])
        or _find_column(columns, ["acess"]),
    }


def export_contracts(excel_path: str, output_path: str, sheet_name: str | None = None) -> int:
    df = _select_sheet(excel_path, sheet_name)
    mapping = _build_mapping(list(df.columns))
    required = ["codigo", "data_inicio", "acessos"]
    missing = [field for field in required if not mapping.get(field)]
    if missing:
        raise ValueError(f"Colunas obrigatorias nao encontradas: {missing}")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    rows_written = 0
    with output.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=OUTPUT_COLUMNS,
            delimiter="\t",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for _, row in df.iterrows():
            codigo = _code(row.get(mapping["codigo"]))
            dt_inicio = _date(row.get(mapping["data_inicio"]))
            acessos = _text(row.get(mapping["acessos"]))
            servicos = _services(row.get(mapping["servicos"]))
            if not codigo or not dt_inicio or not acessos or not servicos:
                continue

            # Mapeamento inicial a partir da planilha atual:
            # DT_CORTE_INICIAL recebe a data de corte inicio.
            # DT_INI e DT_FIM serao obtidos de TB_INSTITUICAO na carga final.
            writer.writerow(
                {
                    "COD_INSTITUICAO": codigo,
                    "COD_COMPARTILHADO": _code(row.get(mapping["cod_compartilhado"])),
                    "NOME_INSTITUICAO": _text(row.get(mapping["nome"])),
                    "NUM_CONTRATO": _text(row.get(mapping["numero_contrato"])),
                    "DT_CORTE_INICIAL": dt_inicio,
                    "FREQUENCIA_CORTE": _text(row.get(mapping["frequencia"])) or "Anual",
                    "SERVICOS_CONTRATADOS": servicos,
                    "NUM_AC_CONTRATADOS": acessos,
                    "VALOR_EXCEDENTE": _text(row.get(mapping["valor_excedente"])),
                    "FL_MONITORAR_CONTRATO": "1",
                }
            )
            rows_written += 1

    return rows_written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exporta a planilha atual para TSV de staging da TB_CONTRATO."
    )
    parser.add_argument("--excel", default=Config.EXCEL_PATH, help="Caminho da planilha fonte.")
    parser.add_argument("--sheet", default=Config.EXCEL_SHEET, help="Nome da aba da planilha.")
    parser.add_argument(
        "--output",
        default="/tmp/stg_contrato_planilha.tsv",
        help="Arquivo TSV de saida para LOAD DATA LOCAL INFILE.",
    )
    args = parser.parse_args()

    total = export_contracts(args.excel, args.output, args.sheet)
    print(f"TSV gerado: {args.output}")
    print(f"Contratos exportados: {total}")


if __name__ == "__main__":
    main()
