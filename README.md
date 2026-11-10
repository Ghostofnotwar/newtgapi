# newtgapi

Python-библиотека для **Telegram Bot API 10.4** — с поддержкой HTML-виджетов, TON Wallet и временных (ephemeral) сообщений. Без зависимостей (только стандартная библиотека Python ≥ 3.10).

> 📚 Анонс API 10.4: [api-changelog#november-9-2026](https://core.telegram.org/bots/api-changelog#november-9-2026)

## Что нового в 10.4 и что реализовано здесь

| Возможность | Методы / типы |
|---|---|
| 📚 HTML-виджеты | `Bot.send_widget`, `Bot.send_shared_widget`, `Bot.edit_message_widget_data`, `Bot.edit_shared_widget_data`, `Bot.answer_widget_query`, `Update.widget_query`, `WidgetQuery`, `Widget`, `SharedWidget` |
| 🏳️ TON Wallet | `WidgetQueryType` (`sign` / `transaction`), `Bot.get_ton_wallet_card`, `TonWalletCard`, `NftSticker`, `TonWalletTransfer`, хелперы `TonSignRequest` / `TonTransactionRequest` |
| 👻 Временные сообщения | `EphemeralMessageParameters` в `send_message`, `answer_callback_query`, `answer_widget_query` |
| ✈️ Форматированные цитаты | расширенный `ReplyParameters` (`quote`, `parse_mode`, `quote_entities`) |
| 🎁 Подарки по названию | `Bot.get_unique_gift(name)` → `UniqueGift` |

## Установка

```bash
pip install newtgapi
# или из исходников:
pip install -e .
```

## Быстрый старт

```python
from newtgapi import Bot
from newtgapi.widgets import HtmlWidget

bot = Bot("123456:ABC-DEF")  # токен бота

html = (
    HtmlWidget(title="Магазин")
    .text("Выберите товар")
    .button("Купить", data="buy:1")
    .ton_sign_button()          # кнопка подписи в TON Wallet
    .render()
)
bot.send_widget(chat_id=42, html=html, width=320, height=240)
```

## Виджеты

```python
from newtgapi import Bot, Dispatcher
from newtgapi.widgets import HtmlWidget, parse_widget_query_data

bot = Bot(TOKEN)
dp = Dispatcher(bot)

@dp.on_widget_query
def _(bot: Bot, update):
    query = update.widget_query
    data = parse_widget_query_data(query.data)   # dict, если data — JSON
    if query.is_ton_wallet:                       # sign / transaction
        bot.answer_widget_query(query.id, text="Подтвердите в TON Wallet")
    else:
        bot.answer_widget_query(query.id, text="Принято!")

dp.poll()  # long polling на getUpdates
```

Общие виджеты — один `widget_id` на много сообщений, обновление в одном месте:

```python
bot.send_shared_widget(chat_id, "shop-main", html)
bot.edit_shared_widget_data("shop-main", {"promo": "10%"})  # обновились все сообщения
```

Обновление виджета в конкретном сообщении:

```python
bot.edit_message_widget_data(chat_id, message_id, {"stock": 3})
```

## TON Wallet

```python
card = bot.get_ton_wallet_card(user_id)
print(card.address, card.balance, len(card.nft_stickers or []))

# Входящий перевод приходит как Message.ton_wallet_transfer
@dp.on_ton_wallet_transfer
def _(bot, update):
    print(update.message.ton_wallet_transfer.amount)
```

## Временные сообщения

Ответ на кнопку, который видит только нажавший пользователь (важно в группах):

```python
from newtgapi.ephemeral import ephemeral_from_callback

@dp.on_callback_query
def _(bot, update):
    query = update.callback_query
    bot.answer_callback_query(
        query.id,
        text="Это видите только вы 👻",
        ephemeral_message_parameters=ephemeral_from_callback(query),
    )
```

## Async

```python
from newtgapi import AsyncBot, Bot

bot = AsyncBot(Bot(TOKEN))
msg = await bot.send_widget(42, "<p>hi</p>")
```

## Примеры

- [`examples/widgets.py`](examples/widgets.py) — виджет-магазин и обработка `WidgetQuery`
- [`examples/shared_widget.py`](examples/shared_widget.py) — общие виджеты
- [`examples/ton_wallet.py`](examples/ton_wallet.py) — карточка кошелька и переводы
- [`examples/ephemeral.py`](examples/ephemeral.py) — временные ответы на кнопки

## Тесты

```bash
pip install -e ".[dev]"
pytest
```

## Структура

```
newtgapi/
  client.py      # Bot / AsyncBot, HTTP-транспорт, все методы API 10.4
  types.py       # типы: WidgetQuery, TonWalletCard, EphemeralMessageParameters, …
  widgets.py     # конструктор HtmlWidget, валидация размеров/данных
  ton_wallet.py  # адреса, суммы, sign/transaction payloads
  ephemeral.py   # хелперы временных сообщений
  dispatcher.py  # маршрутизация апдейтов и polling
  enums.py       # WidgetQueryType и др.
  exceptions.py  # TelegramAPIError и наследники
```

## Примечания по спецификации

Официальная документация Bot API 10.4 недоступна из песочницы разработки, поэтому сигнатуры методов повторяют соглашения существующего Bot API (`sendMessage` → `send_message`, camelCase-алиасы сохранены: `bot.sendWidget(...)` и т.д.). Неизвестные поля ответов сервера сохраняются и возвращаются обратно (`extra`), чтобы библиотека оставалась совместимой с будущими версиями API.

## Лицензия

MIT
