dictionary = {
    "обьектно-ориентированное программирование": "ооп",
    "теория вероятностей и математическая статистика": "тервер",
    "алгебраические структуры": "структуры",
    "элективные курсы по физической культуре": "физ-ра",
    "элективные курсы по физической культуре и спорту": "физ-ра",
    "математический анализ": "матан",
    "военная подготовка": "военка",
    "основы языкознания для цифровых исследований": "языкознание",
    "дифференциальные уравнения": "диффуры",
    "методы программирования": "мп",
    "информатика": "инфа",
    "дискретная математика": "дискретка",
    "алгебра и геометрия": "алгем",
    "практикум по программированию": "практикум",
    "иностранный (немецкий) язык": "ино",
    "история (история россии, всеобщая история)": "история",
    "иностранный  язык": "ино"
}


def shorten(word):
    result = ""
    amount_vowels = 0
    for alpha in word:
        if alpha.lower() in "аеёиоуыэюя" + "aeiouy":
            amount_vowels += 1

        if amount_vowels == 2:
            return result + '.'

        result += alpha
    return result


shorts = ["abr", "start-end", "to-a", "dict"]


def short(text: str, short_type: str, len_to_short: int = 5) -> str:
    if short_type == "abr":
        return ''.join(w[0].upper() for w in text.replace('-', ' ').split())
    elif short_type == "start-end":
        return ' '.join(
            f'{word[:len_to_short]}-{word[-1:]}' if (len(word) - len_to_short) > 3 else word for word in text.split())
    elif short_type == "to-a":
        return ' '.join(shorten(word.strip()) for word in text.replace('-', ' ').split())
    elif short_type == "dict":
        return dictionary.get(text.lower().strip(), text)


if __name__ == '__main__':
    text_for_tests = ["Обьектно-ориентированное программирование",
                      "Теория вероятностей и математическая статистика",
                      "Алгебраические структуры",
                      "Математический анализ",
                      "Элективные курсы по физической культуре",
                      "Основы языкознания для цифровых исследований",
                      "Физика"]

    for test in text_for_tests:
        print(f"{test}:")
        for selected_type in "abr", "start-end", "to-a", "dict":
            print(f"{selected_type}: {short(test, selected_type)}")
        print()
