import datetime
import re
from copy import deepcopy
from itertools import zip_longest

from prettytable import PrettyTable

from BL.abbreviator import short

timetable = ['08:00 - 09:35',
             '09:45 - 11:20',
             '11:30 - 13:05',
             '13:30 - 15:05',

             '15:15 - 16:50',
             '17:00 - 18:35',
             '18:45 - 20:15',
             '20:25 - 21:55']

ru_names_days = {
    "short": ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'],
    "full": ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
}

MAX_PAIRS = len(timetable)


class Room:
    def __init__(self, location: str = "", online=False):
        self.location = location
        self.online = online or bool(re.search(r"on-?line", location.lower()))

    def __str__(self):
        return f"{self.location}"


class Lector:
    def __init__(self, first_name: str = None, last_name: str = None, patronymic: str = None):
        self.first_name = first_name or ""
        self.last_name = last_name or ""
        self.patronymic = patronymic or ""

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.patronymic}"


class Discipline:
    def __init__(self, fullname: str):
        self.fullname = fullname

    def __getitem__(self, type_short) -> str:
        return short(self.fullname, type_short)

    def __str__(self) -> str:
        return self.fullname


class Pair:
    """
    Класс учебной пары (одного занятия)
    """

    def __init__(self, discipline: str,
                 lector: Lector = None,
                 place: Room = None,
                 number: int = 1,
                 pair_type: int = 1,
                 groups: list[str] = None,
                 exist: bool = True):

        """
        Конструктор пары.
        :param exist: логический тип - существует ли данная пара или это окно.

        :param discipline: имя дисциплины.
        :param lector: лектор или практик.
        :param place: место где будет проходить данная пара.
        :param number: номер пары по счёту начиная с первой.
        :param pair_type: тип пары целое число [1- лекция, 2-лабораторная, 3-практика, 4-другое].
        """
        assert 0 < number <= MAX_PAIRS, f"Номер пары не валиден {number} не в диапазоне: ({0}, {MAX_PAIRS}]"
        self.discipline = Discipline(discipline)
        self.lector = lector or Lector()
        self.place = place or Room()
        self.number = number
        self.pair_type = pair_type
        self.groups = [] or groups
        self.exist = exist
        self.time = timetable[self.number - 1]

    def __str__(self):
        if self.exist:
            table = PrettyTable(['Номер', 'Пара', 'Место', 'Чел'])
            table.add_row([self.number, self.discipline, self.place, self.lector])
            return str(table)
        else:
            return f'{self.discipline}'

    def __lt__(self, other):
        return self.number < other.number

    def __int__(self):
        return self.number


class Day:
    """
    Класс одного учебного дня
    """
    HEADERS = ['Номер', 'Время', 'Дисциплина', 'Лектор', 'Место']

    def __init__(self, pairs: list[Pair] = None, date: datetime.date = None, name: str = None):
        """
        Конструктор учебного дня.

        :param date: дата данного дня.
        :param pairs: список пар в данный день
        """
        assert date or name, "У дня должен быть идентификатор (имя или дата)"
        self.__pairs = pairs or []
        self.name = name or ru_names_days['full'][date.weekday()]
        self.date = date

        self.__update()

    @property
    def pairs(self):
        return self.__pairs

    @pairs.getter
    def pairs(self):
        return deepcopy(self.__pairs)

    @pairs.setter
    def pairs(self, pairs: list[Pair]):
        self.__pairs = pairs
        self.__update()

    def __str__(self):
        if not self.__pairs:
            return ""

        table = PrettyTable(Day.HEADERS)

        table.add_rows([[pair.number, timetable[pair.number - 1], pair.discipline, pair.lector, pair.place]
                        for pair in self.__pairs])

        table.align[Day.HEADERS[0]] = "r"

        str_table = str(table)
        str_name = f"Расписание на {self.date or self.name}".center(str_table.index('\n'))

        return str_name + '\n' + str_table

    def __iter__(self):
        return iter(deepcopy(self.__pairs))

    def __int__(self):
        """
        Преобразование к целому числу.

        :return: кол-во существующих пар в данный день.
        """
        return len(tuple(filter(lambda pair: pair.exist, self.__pairs)))

    def __len__(self):
        return int(self)

    def __lt__(self, other):
        """
        Сравнение с другим учебным днём по кол-ву существующих пар.

        :param other: учебный день с которым производим сравнение.
        :return: результат сравнения по кол-ву существующих пар.
        """
        return int(self) < int(other)

    def __update(self):
        """
        Сортирует пары по их номерам и добавляет фиктивные (окна) в случае необходимости.
        """
        buff = []
        number = 1
        try:
            # на всякий случай создаём отсортированный по номеру пар итератор
            pairs = iter(sorted(self.__pairs))
            cur_pair = next(pairs)
            while number <= MAX_PAIRS:
                if number == cur_pair.number:
                    buff.append(cur_pair)
                    cur_pair = next(pairs)
                else:
                    # Добавление фиктивной пары
                    buff.append(Pair('', number=number, exist=False))

                # Если номер пары изменился - двигаемая дальше
                while cur_pair.number == number:
                    # Логика добавления нескольких пар в одно время
                    buff.append(cur_pair)
                    cur_pair = next(pairs)

                number += 1

        except StopIteration:
            pass

        self.__pairs = buff


class Days:
    """Класс списка учебных дней."""
    MAX_DAYS = 6

    def __init__(self, year: datetime.datetime.year, days: list[Day] = None):
        """
        Конструктор списка дней
        :param year: год
        :param days: список дней на этой недели
        """

        self.year = year
        self.__days = days or []
        self.__min_pair_in_days = 0
        self.__max_pair_in_days = 0

        self.__header = None
        self.__check_days()
        self.__update()

    def __check_days(self):
        if len(self.__days) > Days.MAX_DAYS:
            raise UserWarning(f"Количество учебных дней не должно превышать {Days.MAX_DAYS}.")

        roll_dates_names = [day.name for day in self.__days]
        roll_dates_dates = [day.date for day in self.__days]
        if len(roll_dates_names) == len(set(roll_dates_names)):
            self.__header = roll_dates_names
        elif len(roll_dates_dates) == len(set(roll_dates_dates)):
            self.__header = roll_dates_dates
        else:
            raise UserWarning(f"Список дней должен оставаться уникальным по именам или дате")

    @property
    def days(self):
        return self.__days

    @days.setter
    def days(self, days):
        self.__days = days
        self.__check_days()
        self.__update()

    @days.getter
    def days(self):
        return deepcopy(self.__days)

    def __update(self):
        """Пересчитывает все вычисляемые свойства."""
        if self.__days:
            self.__min_pair_in_days = min(int(pair) for day in self.__days for pair in day.pairs if pair.exist)
            self.__max_pair_in_days = max(int(pair) for day in self.__days for pair in day.pairs if pair.exist)
            # print('[!!!]', self.__min_pair_in_days, self.__max_pair_in_days)

    def __str__(self) -> str:
        if not self.__days:
            return ""

        header = ['Время'] + self.__header
        table = PrettyTable(header)

        for time, *pairs in zip_longest(timetable[self.__min_pair_in_days:self.__max_pair_in_days + 1], *self.__days,
                                        fillvalue=Pair('', exist=False)):
            table.add_row([time] + pairs)

        return str(table)

    def __iter__(self):
        return iter(self.days)


def main():
    # Тест класса места проведения пары
    # test_room()

    # тест чела который что-то говорит
    # test_teacher()

    # Проверка работы класса пар
    # test_pair()

    # Проверка работы класса учебного дня
    # test_day()

    # Проверка работы класса списка дней
    test_days()


def test_teacher():
    lector = Lector("his name")
    print(lector, end='\n\n')


def test_room():
    room = Room("https://google.com", online=True)
    print(room, end='\n\n')


def test_days():
    days_names = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб']
    days = [
        Day([Pair("1", number=num) for num in [2, 3]], name=days_names[0]),
        Day([Pair("2", number=num) for num in [6, 7]], name=days_names[1]),
        Day([Pair("3", number=num) for num in [4, 1]], name=days_names[2]),
    ]

    week = Days(datetime.datetime.today().year, days)
    print(week, end='\n\n')


def test_day():
    numbers = [7, 3, 8, 7, 2]
    names_disc = [f"name#{i}" for i in range(len(numbers))]
    pairs = [Pair(names_disc[i], number=numbers[i]) for i in range(len(numbers))]
    day = Day(pairs, date=datetime.date.today())
    print(day, end='\n\n')


def test_pair():
    pair = Pair("Test", Lector("name"), Room("locate"), 1, pair_type=1)
    print(pair, end='\n\n')


if __name__ == '__main__':
    main()
