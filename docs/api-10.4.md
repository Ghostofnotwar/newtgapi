# Bot API 10.4 — соответствие реализации

Источник: [api-changelog#november-9-2026](https://core.telegram.org/bots/api-changelog#november-9-2026)
(официальная документация недоступна из песочницы разработки; сигнатуры
повторяют соглашения существующего Bot API).

## Виджеты

| Метод Bot API | Метод newtgapi | Тип |
|---|---|---|
| `sendWidget` | `Bot.send_widget` / `Bot.sendWidget` | `Message` (с полем `widget`) |
| `sendSharedWidget` | `Bot.send_shared_widget` | `Message` (с полем `shared_widget`) |
| `editMessageWidgetData` | `Bot.edit_message_widget_data` | `bool` |
| `editSharedWidgetData` | `Bot.edit_shared_widget_data` | `bool` |
| `answerWidgetQuery` | `Bot.answer_widget_query` | `bool` |
| `widgetQuery` (update) | `Update.widget_query` | `WidgetQuery` |
| `widgetQueryType` | `WidgetQuery.query_type` + `enums.WidgetQueryType` | `str` |

`WidgetQuery` поля: `id`, `sender_chat`, `chat`, `message`, `data`,
`widget_id`, `shared_widget_id`, `query_type`, `user`.
Свойства: `is_ton_wallet`, `is_sign_request`, `is_transaction_request`.

## TON Wallet

| Метод Bot API | Метод newtgapi | Тип |
|---|---|---|
| `getTonWalletCard` | `Bot.get_ton_wallet_card` | `TonWalletCard` |
| `tonWalletTransfer` (service message) | `Message.ton_wallet_transfer` | `TonWalletTransfer` |
| `widgetQueryType` = sign/transaction | `WidgetQueryType.SIGN` / `.TRANSACTION` | enum |

`TonWalletCard`: `user_id`, `address`, `balance`, `balance_usd`,
`nft_stickers` (`NftSticker`), `is_connected`, `wallet_version`.
`TonWalletTransfer`: `sender_chat`, `sender_user`, `amount`, `comment`,
`transaction_id`, `date`.

## Временные сообщения

`EphemeralMessageParameters(user_id, message_thread_id=None)` —
принимается в `send_message`, `answer_callback_query`,
`answer_widget_query`. Хелперы: `ephemeral_for`,
`ephemeral_from_callback`, `ephemeral_from_widget_query`.

## Прочее

- `ReplyParameters`: добавлены `quote`, `parse_mode`, `quote_entities`
  (цитирование форматированных сообщений).
- `getUniqueGift`: `Bot.get_unique_gift(name)` → `UniqueGift`
  (алиасы `get_unique_gift_by_name`, `getUniqueGift`).
- Premium-имена ботов (`agent`/`ai`/`app`/`game`/`gay`) — поле
  `User.bot_names`, если сервер его возвращает.

## Ограничения (константы в `newtgapi.widgets`)

- `MAX_WIDGET_HTML_SIZE = 64 KiB`
- `MAX_WIDGET_WIDTH/HEIGHT = 4096`
- `MAX_WIDGET_DATA_SIZE = 4096` байт (query / edit data)
