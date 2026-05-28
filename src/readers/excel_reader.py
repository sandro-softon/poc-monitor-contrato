import pandas as pd
import logging
import unicodedata
from typing import List, Dict
from src.config import Config

logger = logging.getLogger(__name__)


class ContractReader:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path

    def _normalize(self, s: str) -> str:
        if not isinstance(s, str):
            return ""
        s = s.strip().lower()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = s.replace(" ", "").replace("_", "")
        return s

    def _find_column(self, cols, keywords):
        for col in cols:
            norm = self._normalize(col)
            for kw in keywords:
                if kw in norm:
                    return col
        return None

    def read_contracts(self) -> List[Dict]:
        """Lê a planilha de contratos e retorna uma lista de dicionários.

        Esta versão adiciona validações, logging e mapeamento flexível de cabeçalhos.
        """
        try:
            # Se uma sheet foi configurada, tente usá-la
            if Config.EXCEL_SHEET:
                df = pd.read_excel(self.excel_path, sheet_name=Config.EXCEL_SHEET)
                if isinstance(df, dict):
                    # caso inesperado, pegue a primeira sheet
                    df = df[next(iter(df.keys()))]
            else:
                # Tenta todas as sheets e escolhe a primeira com colunas relevantes
                xl = pd.read_excel(self.excel_path, sheet_name=None)
                selected = None
                for sheet_name, temp_df in xl.items():
                    cols = list(temp_df.columns)
                    norms = [self._normalize(c) for c in cols]
                    joined = " ".join(norms)
                    if any(
                        k in joined for k in ("codigo", "institu", "acesso", "data")
                    ):
                        selected = temp_df
                        break
                if selected is None:
                    # fallback para a primeira sheet
                    selected = next(iter(xl.values()))
                df = selected
        except FileNotFoundError:
            logger.error(f"Excel file not found: {self.excel_path}")
            return []
        except Exception:
            logger.exception("Error reading Excel file")
            return []

        cols = list(df.columns)

        # Mapear colunas com heurísticas (case-insensitive, sem acentos/espacos)
        mapping = {
            "Codigo Instituicao": self._find_column(cols, ["codigo", "cod", "institu"]),
            "data de corte início": self._find_column(cols, ["inicio"]),
            "data de corte final": self._find_column(cols, ["final", "fim"]),
            "acessos contratados": self._find_column(cols, ["acess"]),
        }

        missing = [k for k, v in mapping.items() if v is None]
        if missing:
            logger.error(
                f"Colunas obrigatórias não encontradas na planilha: {missing}. Colunas disponíveis: {cols}"
            )
            return []

        # Renomear colunas para os nomes esperados pelo analisador
        df = df.rename(columns={v: k for k, v in mapping.items()})

        rows_before = len(df)
        df = df.dropna(
            subset=[
                "Codigo Instituicao",
                "data de corte início",
                "data de corte final",
                "acessos contratados",
            ]
        )
        rows_after = len(df)
        logger.info(f"Lidas {rows_before} linhas, {rows_after} válidas após dropna")

        # Converter datas
        df["data de corte início"] = pd.to_datetime(
            df["data de corte início"], errors="coerce"
        )
        df["data de corte final"] = pd.to_datetime(
            df["data de corte final"], errors="coerce"
        )

        # Identificar linhas com datas inválidas
        nat_mask = df["data de corte início"].isna() | df["data de corte final"].isna()
        if nat_mask.any():
            invalid = df[nat_mask]
            for idx, row in invalid.iterrows():
                inst = row.get("Codigo Instituicao", "N/A")
                inicio = row.get("data de corte início", "N/A")
                final = row.get("data de corte final", "N/A")
                logger.warning(
                    f"Linha {idx} ignorada (data inválida): "
                    f"Codigo Instituicao={inst}, inicio={inicio}, final={final}"
                )
            df = df[~nat_mask]

        # Normalizar acessos contratados para numérico (fallback 0)
        df["acessos contratados"] = pd.to_numeric(
            df["acessos contratados"], errors="coerce"
        ).fillna(0)

        return df.to_dict("records")
