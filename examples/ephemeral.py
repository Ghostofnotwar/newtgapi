"""Пример: временные (ephemeral) сообщения (Bot API 10.4).

Нажатие кнопки в групповом чате отвечает только нажавшему
пользователю — остальные участники чата сообщение не видят.

Запуск:  BOT_TOKEN=... python examples/ephemeral.py
"""

import os

from newtgapi import Bot, Dispatcher
from newtgapi.ephemeral import ephemeral_from_callback
from newtgapi.types import InlineKeyboardButton, InlineKeyboardMarkup


def main() -> None:
    bot = Bot(os.environ["BOT_TOKEN"])
    dp = Dispatcher(bot)

    @dp.on_message
    def _(b: Bot, update) -> None:
        msg = update.message
        if msg and msg.text == "/menu":
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Мой профиль", callback_data="profile")]
                ]
            )
            b.send_message(msg.chat.id, "Меню:", reply_markup=markup)

    @dp.on_callback_query
    def _(b: Bot, update) -> None:
        query = update.callback_query
        if query.data == "profile":
            # Видно только пользователю, нажавшему кнопку.
            b.answer_callback_query(
                query.id,
                text="Это видите только вы 👻",
                ephemeral_message_parameters=ephemeral_from_callback(query),
            )

    dp.poll()


if __name__ == "__main__":
    main()
