"""newtgapi — Python library for the Telegram Bot API 10.4.

Highlights of API 10.4 implemented here:

* HTML widgets — :meth:`Bot.send_widget`, :meth:`Bot.send_shared_widget`,
  :meth:`Bot.edit_message_widget_data`, :meth:`Bot.edit_shared_widget_data`,
  :meth:`Bot.answer_widget_query` and the ``Update.widget_query`` type.
* TON Wallet — ``WidgetQueryType`` (``sign`` / ``transaction``),
  :meth:`Bot.get_ton_wallet_card`, ``TonWalletCard`` / ``TonWalletTransfer``.
* Ephemeral messages — ``EphemeralMessageParameters`` accepted by
  ``send_message``, ``answer_callback_query`` and ``answer_widget_query``.
* Formatted quotes — extended ``ReplyParameters`` (``quote`` + entities).
* Gifts by name — :meth:`Bot.get_unique_gift`.

Quick start::

    from newtgapi import Bot
    from newtgapi.widgets import HtmlWidget

    bot = Bot("123456:ABC-DEF")
    html = HtmlWidget(title="Магазин").text("Выберите товар").button("Купить", "buy:1").render()
    bot.send_widget(chat_id=42, html=html, width=320, height=240)
"""

from .client import API_BASE, AsyncBot, Bot, HttpTransport
from .dispatcher import AsyncDispatcher, Dispatcher
from .enums import ParseMode, TonWalletAction, WidgetQueryType
from .ephemeral import ephemeral_for, ephemeral_from_callback, ephemeral_from_widget_query
from .exceptions import (
    ForbiddenError,
    NetworkError,
    NewTgApiError,
    NotFoundError,
    TelegramAPIError,
    TooManyRequestsError,
    UnauthorizedError,
    ValidationError,
)
from .ton_wallet import (
    TonSignRequest,
    TonTransactionRequest,
    format_ton_amount,
    is_valid_ton_address,
    summarize_transfer,
    summarize_wallet_card,
    validate_ton_address,
)
from .types import (
    CallbackQuery,
    Chat,
    EphemeralMessageParameters,
    Message,
    NftSticker,
    ReplyParameters,
    SharedWidget,
    TonWalletCard,
    TonWalletTransfer,
    UniqueGift,
    Update,
    User,
    Widget,
    WidgetQuery,
)
from .widgets import HtmlWidget, WidgetButton, parse_widget_query_data

__version__ = "10.4.0"
__all__ = [
    "API_BASE",
    "AsyncBot",
    "AsyncDispatcher",
    "Bot",
    "CallbackQuery",
    "Chat",
    "Dispatcher",
    "EphemeralMessageParameters",
    "ForbiddenError",
    "HtmlWidget",
    "HttpTransport",
    "Message",
    "NetworkError",
    "NewTgApiError",
    "NftSticker",
    "NotFoundError",
    "ParseMode",
    "ReplyParameters",
    "SharedWidget",
    "TelegramAPIError",
    "TonSignRequest",
    "TonTransactionRequest",
    "TonWalletAction",
    "TonWalletCard",
    "TonWalletTransfer",
    "TooManyRequestsError",
    "UnauthorizedError",
    "UniqueGift",
    "Update",
    "User",
    "ValidationError",
    "Widget",
    "WidgetButton",
    "WidgetQuery",
    "WidgetQueryType",
    "ephemeral_for",
    "ephemeral_from_callback",
    "ephemeral_from_widget_query",
    "format_ton_amount",
    "is_valid_ton_address",
    "parse_widget_query_data",
    "summarize_transfer",
    "summarize_wallet_card",
    "validate_ton_address",
]
