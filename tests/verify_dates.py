from datetime import datetime
from src.core.date_utils import get_current_cycle

def test():
    # Test 1: Monthly
    start = datetime(2024, 1, 15)
    now = datetime(2026, 3, 20)
    inicio, fim = get_current_cycle(start, "Mês", now)
    print(f"Monthly (15/01/24, Ref: 20/03/26): {inicio} a {fim}")
    assert inicio == datetime(2026, 3, 15)
    assert fim == datetime(2026, 4, 15)

    # Test 2: Semester
    inicio, fim = get_current_cycle(start, "Semestre", now)
    print(f"Semester (15/01/24, Ref: 20/03/26): {inicio} a {fim}")
    assert inicio == datetime(2026, 1, 15)
    assert fim == datetime(2026, 7, 15)

    # Test 3: Annual
    inicio, fim = get_current_cycle(start, "Anual", now)
    print(f"Annual (15/01/24, Ref: 20/03/26): {inicio} a {fim}")
    assert inicio == datetime(2026, 1, 15)
    assert fim == datetime(2027, 1, 15)

    print("ALL TESTS PASSED!")

if __name__ == "__main__":
    test()
