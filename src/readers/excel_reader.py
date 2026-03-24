import pandas as pd
from typing import List, Dict

class ContractReader:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path

    def read_contracts(self) -> List[Dict]:
        """Lê a planilha de contratos e retorna uma lista de dicionários."""
        df = pd.read_excel(self.excel_path)
        
        # Filtra apenas registros válidos (ignora linhas vazias sem data de corte ou instituição)
        df = df.dropna(subset=['Codigo Instituicao', 'data de corte início', 'data de corte final', 'acessos contratados'])
        
        # Opcional: Converter colunas de data (caso o pandas não as converta automaticamente)
        df['data de corte início'] = pd.to_datetime(df['data de corte início'], errors='coerce')
        df['data de corte final'] = pd.to_datetime(df['data de corte final'], errors='coerce')
        
        return df.to_dict('records')
