import pandas as pd
from datetime import datetime
from typing import Tuple

def get_current_cycle(start_date: datetime, frequency: str, now: datetime = None) -> Tuple[datetime, datetime]:
    """
    Calcula o ciclo atual de um contrato baseando-se no dia do início original e na frequência.
    
    Args:
        start_date: A data original de início do contrato (baseline).
        frequency: Uma das strings: 'Mês', 'Semestre' ou 'Anual'.
        now: A data de referência atual (opcional, defaults to now).
        
    Returns:
        Um par (data_inicio_ciclo, data_fim_ciclo).
    """
    if now is None:
        now = datetime.now()
    
    # Normaliza as entradas para Pandas Timestamps para facilitar cálculos com DateOffset
    baseline = pd.to_datetime(start_date)
    reference = pd.to_datetime(now)
    
    # Mapeia frequências para offsets de meses
    months_map = {
        'mês': 1,
        'mes': 1,
        'mensal': 1,
        'semestre': 6,
        'semestral': 6,
        'anual': 12
    }
    
    # Se não encontrar frequência válida, assume Anual como fallback seguro
    delta_months = months_map.get(frequency.strip().lower(), 12)
    
    # Caso 1: Se o contrato ainda não começou
    if reference < baseline:
        next_cycle = baseline + pd.DateOffset(months=delta_months)
        return baseline.to_pydatetime(), next_cycle.to_pydatetime()
    
    # Caso 2: Contrato em andamento - encontrar o intervalo atual
    # Começamos do baseline e avançamos em saltos de N meses até passar o 'reference'
    curr_start = baseline
    while True:
        next_cycle = curr_start + pd.DateOffset(months=delta_months)
        if next_cycle > reference:
            # Encontramos o ciclo que cobre o momento atual
            return curr_start.to_pydatetime(), next_cycle.to_pydatetime()
        curr_start = next_cycle
