"""Парсинг дат"""
from datetime import date

MONTHS = [
    ['январь'],
    ['февраль'],
    ['март'],
    ['апрель'],
    ['май'],
    ['июнь'],
    ['июль'],
    ['август'],
    ['сентябрь'],
    ['октябрь'],
    ['ноябрь'],
    ['декабрь'],
]


def parse_month_year(line: str) -> date:
    """Получить номер месяца и год из строки на криллице"""

    words = line.strip().lower().split(' ')
    if len(words) != 2:
        raise ValueError(f'Невозможно распарсить месяц и год, {words}')

    month = 0
    for n, mon in enumerate(MONTHS, start=1):
        if words[0] in mon:
            month = n
            break

    if month == 0:
        raise ValueError(f'Неудалось извлечь месяц {words}')

    year = int(words[1])
    return date(year=year, month=month, day=1)


if __name__ == '__main__':
    d = parse_month_year('ДЕКАБРЬ 2024')
    d = d.replace(day=2)
    print(d)
