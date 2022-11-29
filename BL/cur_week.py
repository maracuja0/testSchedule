from datetime import date, timedelta


def get_cur_week(cur_date: date = date.today()):
    year = cur_date.year if 9 <= cur_date.month <= 12 else cur_date.year - 1
    first_september = date(year, 9, 1)
    date_first_learn_week = first_september - timedelta(days=first_september.weekday())
    return ((cur_date - date_first_learn_week) // 7).days + 1


if __name__ == '__main__':
    print(get_cur_week())
