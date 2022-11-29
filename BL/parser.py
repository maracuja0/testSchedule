"""
Данный модуль занимается получением расписания на конкретную неделю по полученной ссылке со следующих сайтов:
https://ssau.ru/
"""
import datetime
import logging
import math
import os
import re

import requests
from bs4 import BeautifulSoup, FeatureNotFound

from BL.cur_week import get_cur_week
from BL.schedule import Days, Pair, Lector, Room, Day

tmp_path = 'tmp'


def clear():
    for filename in os.listdir(tmp_path):
        if filename.startswith(datetime.datetime.now().strftime('%d-%m-%y')):
            continue
        os.remove(os.path.join(tmp_path, filename))


def get_source(url: str) -> str:
    group_id = match.group(1) if (match := re.search(r"groupId=(\d+)", url)) else None
    selected_week = match.group(1) if (match := re.search(r"selectedWeek=(\d+)", url)) else get_cur_week()

    if not group_id:
        raise AttributeError("Некорректная ссылка")

    filename = os.path.join(tmp_path, f"{datetime.datetime.now().strftime('%d-%m-%y')}_{group_id}.html")
    if not os.path.exists(filename):
        if not os.path.isdir(tmp_path):
            os.mkdir(tmp_path)
        request = requests.get(f"https://ssau.ru/rasp?groupId={group_id}&selectedWeek={selected_week}")
        if request.status_code == 200:
            with open(filename, mode='w', encoding='utf-8') as f:
                f.write(request.text)
            logging.info(f"Успешно сохранено с именем: {filename}.")

    with open(filename, mode='r', encoding='utf-8') as f:
        return f.read()


def reshape(roll, length):
    """
    Создаёт из одномерного массива двумерный, объединяя в строку по {param} элементов.
    :param roll: исходный список.
    :param length: по сколько элементов объединять.
    :return: новый список с объединёнными массивами
    """
    return [roll[(cur_pos := i * length):cur_pos + length] for i in range(math.ceil(len(roll) / length))]


def transpose(roll):
    return list(zip(*roll))


def parse(schedule_url: str) -> tuple[str, Days]:
    """
    Возвращает расписание на неделю.
    :return: объект списка учебных дней
    """
    clear()

    src = get_source(schedule_url)

    try:
        soup = BeautifulSoup(src, "lxml")
    except FeatureNotFound:
        soup = BeautifulSoup(src, "html.parser")

    group = match.text.strip() if (match := soup.find("h2", class_="h2-text info-block__title")) else '?'

    days_dates: list[datetime.date] = []

    # Кол-во дней в учебной недели
    amount_days = 6

    pairs = []
    # добавляем пары или дату пробегая одну за другой ячейки таблицы (данная таблица читается построчно)
    for item in soup.find_all("div", class_="schedule__item"):

        # Случай когда рассматриваемая ячейка является заголовком (header)
        if "schedule__head" in item["class"]:

            if date := item.find("div", class_="caption-text schedule__head-date"):
                day, month, year = map(int, date.text.strip().split('.'))
                days_dates.append(datetime.date(year, month, day))
            continue

        # Сразу считаем номер текущей пары
        number_pair = len(pairs) // amount_days + 1

        # Случай когда рассматриваемая ячейка является парой (содержит имя лекции)
        if lesson := item.find("div", class_="schedule__lesson"):

            # Перебор всех типов пар
            pair_type = 1
            while True:
                var = f"body-text schedule__discipline lesson-color lesson-color-type-{pair_type}"
                if discipline_name := lesson.find("div", class_=var):
                    discipline_name = discipline_name.text.strip()
                    break
                pair_type += 1

            if place := lesson.find("div", class_="caption-text schedule__place"):
                place = place.text.strip()

            if teacher := lesson.find("div", class_="schedule__teacher"):
                teacher = teacher.text.strip()

            if groups := lesson.find("div", class_="schedule__groups"):
                groups = groups.text.strip().split()

            pairs.append(Pair(discipline_name, Lector(teacher), Room(place), number_pair, pair_type, groups))

        # В противном случае если ячейка пуста считаем пару окном
        elif item.text == "":
            pairs.append(Pair("", number=number_pair, exist=False))

        # Пропускаем если ячейка не подходит не под один из вариантов
        else:
            logging.debug('Необработанная непустая ячейка')

    days = [Day(pairs, date) for date, *pairs in zip(days_dates, *reshape(pairs, amount_days))]
    d = Days(datetime.date.today().year, days)
    return group, d


def main():
    days = parse('https://ssau.ru/rasp?groupId=799359428')
    # print(days)

    for day in days:
        print(day, end='\n\n')


if __name__ == '__main__':
    main()
