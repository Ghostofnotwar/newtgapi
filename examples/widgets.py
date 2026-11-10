"""Пример: HTML-виджеты (Bot API 10.4).

Запуск:  BOT_TOKEN=... python examples/widgets.py
"""

import os

from newtgapi import Bot, Dispatcher
from newtgapi.widgets import HtmlWidget, parse_widget_query_data


def main() -> None:
    bot = Bot(os.environ["BOT_TOKEN"])
    dp = Dispatcher(bot)

    @dp.on_message
    def _(b: Bot, update) -> None:
        if update.message and update.message.text == "/shop":
            html = (
                HtmlWidget(title="Магазин")
                .text("Выберите товар:")
                .button("Товар 1 — 10 TON", data="buy:1")
                .button("Товар 2 — 20 TON", data="buy:2")
                .ton_sign_button()
                .render()
            )
            b.send_widget(update.message.chat.id, html, width=360, height=280)

    @dp.on_widget_query
    def _(b: Bot, update) -> None:
        query = update.widget_query
        data = parse_widget_query_data(query.data)
        print(f"widget query: type={query.query_type} data={data!r}")
        if query.is_ton_wallet:
            b.answer_widget_query(query.id, text="Откройте TON Wallet для подтверждения")
        else:
            b.answer_widget_query(query.id, text="Принято!")

    dp.poll()


if __name__ == "__main__":
    main()
