"""Парсилка гугл диска"""

import re
import httpx
from bs4 import BeautifulSoup

from core.utils import date as date_parse
from core.models import update_schedule


GROUP_PATTERN = r'^[1-4]-[1-2]\w[19][1]{,1}$'
PAIR_PATTERN = r'^[1-9]$'


async def get_response(url: str) -> str:
    """асинхронное отправка запроса"""

    async with httpx.AsyncClient() as client:
        return await client.get(
            url=url,
            timeout=60,
        )


async def get_content_by_folder(folder_id: str) -> list:
    """Получить содержимое гугл папки"""

    response = await get_response(
            url=f"https://drive.google.com/drive/folders/{folder_id}"
    )
    folder_soup = BeautifulSoup(
        response.text,
        'html.parser',
    )

    result = []
    for item_soup in folder_soup.find_all('div', attrs={'class': 'WYuW0e'}):
        result.append({
            'name': item_soup.find('div', attrs={'class': 'KL4NAf'}).text,
            'id': item_soup.get('data-id'),
        })
    return result


def group_name_parse(context: dict):
    """Парсинг имени группы"""

    if context['drop_groups']:
        context['groups'] = []
        context['group_ind'] = -1
        context['drop_groups'] = False

    if context['value_rep'] == '':
        context['groups'].append(None)
    else:
        context['groups'].append(context['value_rep'])
        context['schedule'][context['value_rep']] = {}


def pair_parse(context: dict):
    """парсинг номера пары"""

    context['group_ind'] += 1
    if context['group_ind'] >= len(context['groups']):
        context['group_ind'] = 0
    context['drop_groups'] = True

    if context['state'] != 0:
        context['state'] = 0

    if context['groups'][context['group_ind']]:
        try:
            context['last_pair'] = int(context['value_rep'])
            group_name = context['groups'][context['group_ind']]
            group = context['schedule'][group_name]
            if context['last_pair'] not in group:
                group[context['last_pair']] = {}
        except ValueError:
            context['last_pair'] = None
    context['state'] = 1


def disc_or_aud_parse(key: str, context: dict):
    """Парскинг дисциплины или аудитории столбца"""

    if context['groups'][context['group_ind']] is None:
        return

    if context['value_rep'] == '':
        return

    group_name = context['groups'][context['group_ind']]
    group = context['schedule'][group_name]

    # Парсинг объединенного столбца
    for i in range(1, int(context['cell'].get('rowspan'))):
        group[context['last_pair'] + i] = {key: context['value']}

    if key not in group[context['last_pair']]:
        group[context['last_pair']][key] = context['value']


def discipline_parse(context: dict):
    """Парсинг названия дисциплины"""

    disc_or_aud_parse('discipline', context)
    context['state'] = 2


def auditory_parse(context: dict):
    """Парсинг номера аудитории"""

    disc_or_aud_parse('auditory', context)
    context['state'] = 0


def clear_schedule(context: dict):
    """Очистка пар без занятий"""

    schedule = context['schedule']
    for group in schedule:
        keys = list(schedule[group].keys())
        for pair in keys:
            if not schedule[group][pair]:
                del schedule[group][pair]


def row_parse(row, context: dict):
    """Парсинг строки таблицы"""
    prev_group = False
    for cell in row.find_all('td'):
        context['cell'] = cell
        value = cell.text.strip().replace('. ', '.')
        while '----' in value:
            value = value.replace('----', '---')
        context['value'] = value
        context['value_rep'] = value_rep = value.replace(' ', '')

        # Пропуск ячейки после название группы
        if prev_group:
            prev_group = False
            continue
        cond1 = int(cell.get('colspan')) > 1
        cond2 = re.match(GROUP_PATTERN, value_rep)
        cond3 = value_rep == ''
        cond4 = context['group_ind'] == -1

        if cond1 and (cond2 or cond3) and cond4:
            group_name_parse(context)
            prev_group = True

        elif re.match(PAIR_PATTERN, value_rep) or context['state'] == 0:
            pair_parse(context)

        elif context['state'] == 1:
            discipline_parse(context)

        elif context['state'] == 2:
            auditory_parse(context)


async def get_schedule_by_doc(doc_id: str) -> dict:
    """Получить расписание с диска"""

    response = await get_response(
        url=f"https://docs.google.com/document/d/{doc_id}/export?format=html"
    )

    file_content = BeautifulSoup(
        response.content,
        'html.parser'
    )

    context = {
        'schedule': {},
        'groups': [],
        'last_pair': 0,
        'drop_groups': False,
    }

    for table in file_content.find_all('table'):
        for row in table.find_all('tr'):
            context['group_ind'] = -1
            context['state'] = 0
            row_parse(row, context)

    clear_schedule(context)

    return context['schedule']


async def run():
    """Запуск парсина расписания"""
    root_folder = await get_content_by_folder(
        '1Z8V1jh0OZuW-e3m-O05D0n88_OdDPyTV'
    )

    for folder in root_folder:
        date = date_parse.parse_month_year(folder['name'])
        for doc in await get_content_by_folder(folder['id']):

            day = int(doc['name'].strip().split(' ')[0])
            date = date.replace(day=day)
            schedule_data = await get_schedule_by_doc(doc['id'])
            await update_schedule(
                date=date,
                doc_id=doc['id'],
                schedule_data=schedule_data
            )
