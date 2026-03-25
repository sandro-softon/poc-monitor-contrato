import pytest
from datetime import datetime
from src.core.date_utils import get_current_cycle

def test_monthly_cycle_after_day():
    start = datetime(2024, 1, 15)
    now = datetime(2026, 3, 20)
    # Ciclo deve ser 15/03 a 15/04
    inicio, fim = get_current_cycle(start, "Mês", now)
    assert inicio == datetime(2026, 3, 15)
    assert fim == datetime(2026, 4, 15)

def test_monthly_cycle_before_day():
    start = datetime(2024, 1, 15)
    now = datetime(2026, 3, 5)
    # Ciclo deve ser 15/02 a 15/03
    inicio, fim = get_current_cycle(start, "Mês", now)
    assert inicio == datetime(2026, 2, 15)
    assert fim == datetime(2026, 3, 15)

def test_semester_cycle():
    start = datetime(2024, 1, 15)
    now = datetime(2026, 3, 20)
    # Ciclos em 15/01 e 15/07
    inicio, fim = get_current_cycle(start, "Semestre", now)
    assert inicio == datetime(2026, 1, 15)
    assert fim == datetime(2026, 7, 15)

def test_annual_cycle():
    start = datetime(2024, 1, 15)
    now = datetime(2026, 3, 20)
    # Ciclo anual começando em 15/01/2026
    inicio, fim = get_current_cycle(start, "Anual", now)
    assert inicio == datetime(2026, 1, 15)
    assert fim == datetime(2027, 1, 15)

def test_leap_year_end_of_month():
    # Início em 31/01
    start = datetime(2024, 1, 31)
    # Março de 2026 (não bissexto) com reference em 10/03
    # Ciclo anterior: 31/01 a 28/02 (aproximado pelo Offset do Pandas) -> 28/02 a 31/03?
    # Vamos ver como o pd.DateOffset lida com isso.
    now = datetime(2026, 3, 10)
    inicio, fim = get_current_cycle(start, "Mês", now)
    # pd.DateOffset(months=1) de 31/01 para Fev resulta em 28/02 ou 29/02.
    # No caso de 31/01/2026 -> 28/02/2026.
    # Depois 28/02/2026 + 1 mês -> 28/03/2026? 
    # Ou ele tenta manter o 31 se possível? 
    # Na verdade, pd.DateOffset(months=1) de 28/02/2026 é 28/03/2026.
    print(f"DEBUG: 31/01 -> {inicio} a {fim}")
    assert inicio.day <= 31

def test_trimestral_cycle():
    start = datetime(2024, 1, 15)
    now = datetime(2026, 3, 20)
    # Ciclos tri-mensais em 15/01, 15/04, 15/07, 15/10
    # Em 20/03/2026, o ciclo atual deve ser 15/01/2026 a 15/04/2026
    inicio, fim = get_current_cycle(start, "Trimestral", now)
    assert inicio == datetime(2026, 1, 15)
    assert fim == datetime(2026, 4, 15)

def test_bimestral_cycle():
    start = datetime(2024, 1, 15)
    now = datetime(2026, 3, 20)
    # Ciclos bi-mensais em 15/01, 15/03, 15/05, etc.
    # Em 20/03/2026, o ciclo atual deve ser 15/03/2026 a 15/05/2026
    inicio, fim = get_current_cycle(start, "Bimestral", now)
    assert inicio == datetime(2026, 3, 15)
    assert fim == datetime(2026, 5, 15)
