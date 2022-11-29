import asyncio
import datetime
import logging

import requests
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from BL.cur_week import get_cur_week
from BL.parser import parse
from DB.db import BotDB
from settings import config

BOT_DB = BotDB(config.database_filename)
exampleURL = 'https://ssau.ru/rasp?groupId='

HELP_COMMAND = """
<b>Доступны следующие команды:</b>\n
• <b>/help</b> - выводит текущее сообщение
• <b>/start</b> - для первого знакомства
• <b>/get</b> - для получения расписания на текущую неделю
• <b>/set</b> - для смены ссылки расписания
"""


class TelegramBot:
    bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher(bot)

    @staticmethod
    async def run():
        await TelegramBot.dp.start_polling(TelegramBot.bot)

    @staticmethod
    @dp.message_handler(commands="start")
    async def cmd_start(message: types.Message):
        logging.debug(f"start {message.from_user.id = } {datetime.datetime.now()}")

        if not BOT_DB.user_exists(message.from_user.id):
            BOT_DB.add_user(message.from_user.id, message.from_user.full_name)
            logging.info(f"add new user: {message.from_user.id = }")

            await message.answer(f'Привет, {message.from_user.first_name}!\n'
                                 f'Я умею показывать расписание твоей группы прямо в Telegram!\n'
                                 f'Отправь мне ссылку в формате {exampleURL} расписания, '
                                 f'чтобы я мог запомнить его для тебя :)')
        else:
            await message.answer(f"Всё ок, {message.from_user.first_name}, я тебя помню.\n"
                                 f"Твоя ссылка на расписание:\n{BOT_DB.get_schedule_link(message.from_user.id)}")

    @staticmethod
    @dp.message_handler(regexp=r"[Пп]омощь|[Hh]elp")
    async def cmd_help(message: types.Message):
        logging.debug(f"help {message.from_user.id = } {datetime.datetime.now()}")

        await message.answer(text=HELP_COMMAND)

    @staticmethod
    @dp.message_handler(regexp=r"Получить расписание|get")
    async def cmd_get(message: types.Message):
        logging.debug(f"get {message.from_user.id = } {datetime.datetime.now()}")

        if BOT_DB.user_exists(message.from_user.id):
            schedule_url = BOT_DB.get_schedule_link(message.from_user.id)

            if schedule_url:

                group, days = parse(schedule_url)
                await message.answer("Готово 😉\n"
                                     f"Расписания для {group} на {get_cur_week()} неделю:")

                type_short = 'dict'
                for day in days:
                    msg = f"<b>{day.name.title()}</b> - <i>{day.date.strftime('%d.%m.%Y')}</i>\n\n"
                    if len(day):
                        pairs = []
                        exists = False
                        for pair in reversed(list(day)):

                            if pair.exist:
                                exists = True

                            if not exists:
                                continue

                            if pair.exist:
                                pairs.append(f"<b>{pair.number}</b> | {pair.time} | "
                                             f"<b><u>{pair.discipline[type_short]}</u></b> | "
                                             f"{'online' if pair.place.online else pair.place} | ")
                            else:
                                pairs.append(f"<b>{pair.number}</b> | {pair.time} | {'-' * 15}")

                        pairs.reverse()
                        msg += '\n'.join(pairs)
                    else:
                        msg += 'В этот день нет пар - чилим 😎'
                    await message.answer(msg)
            else:
                await message.answer("Сначала отправь мне ссылку на расписание")
        else:
            await message.answer("Но мы же ещё не знакомы 🤨.\nНапиши команду /start для знакомства.")

    @staticmethod
    @dp.message_handler(commands="set")
    async def cmd_set(message: types.Message):
        logging.debug(f"help {message.from_user.id = } {datetime.datetime.now()}")

        await message.answer(f'Просто скинь мне ссылку на твоё расписание в следующем формате:\n'
                             f'{exampleURL}#########, где вместо решёток id твоей группы')

    @staticmethod
    @dp.message_handler()
    async def set_schedule_link(message: types.Message):
        schedule_url = message.text
        if exampleURL in schedule_url:
            if requests.get(schedule_url).status_code == 200:
                if BOT_DB.user_exists(message.from_user.id):
                    BOT_DB.set_schedule_link(message.from_user.id, schedule_url)

                    kb = ReplyKeyboardMarkup(resize_keyboard=True)
                    button_get_schedule = KeyboardButton(text="Получить расписание")
                    button_help = KeyboardButton(text="Помощь")
                    kb.add(button_get_schedule, button_help)

                    await message.answer(
                        "Отлично, я запомнил твою группу, для получения расписания выбери кнопку на клавиатуре",
                        reply_markup=kb)
                else:
                    await message.answer("Сперва нужно бы познакомиться, отправь команду /start для знакомства.")
        else:
            await message.answer("Извини я не знаю что ответить")


async def main():
    bot = TelegramBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
