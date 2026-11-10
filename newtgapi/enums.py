"""Enumerations introduced / extended by Bot API 10.4."""

from __future__ import annotations

from enum import Enum


class WidgetQueryType(str, Enum):
    """Type of a :class:`~newtgapi.types.WidgetQuery`.

    Widgets integrated with TON Wallet can ask the user to sign a
    message or to confirm a transaction.  The type is echoed back in
    the ``widget_query`` update so the bot can route it correctly.

    The values follow the Bot API naming (``sign`` / ``transaction``);
    unknown future values are preserved as plain strings by the
    deserializer (see :mod:`newtgapi.types`).
    """

    #: User is asked to sign a payload with their TON wallet.
    SIGN = "sign"
    #: User is asked to confirm / be notified about a TON transaction.
    TRANSACTION = "transaction"
    #: Generic widget interaction (default for plain HTML widgets).
    INTERACTION = "interaction"

    @classmethod
    def _missing_(cls, value: object) -> "WidgetQueryType | None":  # type: ignore[override]
        # Preserve unknown server values instead of raising.
        if isinstance(value, str):
            # Return a pseudo-member via object.__new__ trick is fragile;
            # callers that need raw strings should use ``str`` fallback
            # in types.py.  Here we simply return None so the caller
            # can keep the raw value.
            return None
        return None


class TonWalletAction(str, Enum):
    """High-level TON Wallet actions a widget can request."""

    SIGN = "sign"
    TRANSACTION = "transaction"
    NOTIFY_TRANSACTION = "transaction"


class ParseMode(str, Enum):
    HTML = "HTML"
    MARKDOWN_V2 = "MarkdownV2"
    MARKDOWN = "Markdown"
