import sqlite3


class BotDB:

    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def user_exists(self, user_id):
        """Проверяем, есть ли юзер в базе"""
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def get_user_id(self, user_id):
        """Достаем id юзера в базе по его user_id"""
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchone()[0]

    def add_user(self, user_id, fullname):
        """Добавляем юзера в базу"""
        self.cursor.execute("INSERT INTO `users` (`user_id`, `fullname`) VALUES (?, ?)", (user_id, fullname))
        return self.connection.commit()

    def set_schedule_link(self, user_id, link: str):
        """Записываем ссылку на расписание для данного пользователя"""
        self.cursor.execute("UPDATE `users` SET `schedule_link` = (?) WHERE user_id = (?)", (link, user_id))
        return self.connection.commit()

    def get_schedule_link(self, user_id):
        """Получаем ссылку на расписание для данного пользователя"""
        result = self.cursor.execute("SELECT `schedule_link` FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchone()[0]

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()

    def __del__(self):
        self.close()


if __name__ == '__main__':
    bot_db = BotDB('schedule.db')
    telegram_user_id = 12345
    user_fullname = "first last olala"
    schedule_link = "https://google.com"
    if not bot_db.user_exists(telegram_user_id):
        bot_db.add_user(telegram_user_id, user_fullname)
        bot_db.set_schedule_link(telegram_user_id, schedule_link)
    print(bot_db.get_schedule_link(telegram_user_id))
    bot_db.close()
