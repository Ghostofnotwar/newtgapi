"""Пример: общие (shared) виджеты (Bot API 10.4).

Один widget_id переиспользуется в разных сообщениях; одно
обновление через edit_shared_widget_data мгновенно меняет все.

Запуск:  BOT_TOKEN=... python examples/shared_widget.py
"""

import os

from newtgapi import Bot
from newtgapi.widgets import HtmlWidget


def main() -> None:
    bot = Bot(os.environ["BOT_TOKEN"])
    widget_id = "shop-main"

    html = HtmlWidget(title="Магазин").text("Скидка 10%!").button("Купить", "buy:1").render()

    # Отправить один и тот же виджет в два чата.
    bot.send_shared_widget(111, widget_id, html, width=360, height=240)
    bot.send_shared_widget(222, widget_id, html, width=360, height=240)

    # Обновить централизованно — оба сообщения изменятся.
    bot.edit_shared_widget_data(widget_id, {"promo": "10%"})
    print("shared widget updated everywhere")


if __name__ == "__main__":
    main()
