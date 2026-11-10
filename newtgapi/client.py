"""Bot API client (sync + async) with Bot API 10.4 methods.

The client is transport-agnostic: pass a custom ``transport`` in
tests to avoid network access.  The default transport uses only the
standard library (``urllib``), so the package has zero dependencies.

Method naming follows the Bot API: Python ``snake_case`` primary,
``camelCase`` aliases are provided for every public method
(e.g. ``bot.send_widget`` == ``bot.sendWidget``).
"""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from typing import Any, Callable, Protocol

from .exceptions import (
    ForbiddenError,
    NetworkError,
    NotFoundError,
    TelegramAPIError,
    TooManyRequestsError,
    UnauthorizedError,
    ValidationError,
)
from .types import (
    EphemeralMessageParameters,
    Message,
    ReplyParameters,
    TonWalletCard,
    UniqueGift,
    Update,
    User,
)
from .widgets import validate_widget_data, validate_widget_html, validate_widget_size

API_BASE = "https://api.telegram.org"


class Transport(Protocol):
    def request(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class HttpTransport:
    """Default stdlib HTTP transport."""

    def __init__(self, token: str, *, base_url: str = API_BASE, timeout: float = 30.0) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/bot{self.token}/{method}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise _raise_for_body(raw, exc.code) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise NetworkError(str(exc)) from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise NetworkError(f"invalid JSON from Bot API: {raw[:200]!r}") from exc
        if not data.get("ok"):
            raise _raise_for_body(raw, data.get("error_code"))
        return data.get("result")


def _raise_for_body(raw: str, status: int | None = None) -> TelegramAPIError:
    try:
        data = json.loads(raw)
    except Exception:
        return TelegramAPIError(f"HTTP {status}: {raw[:200]}", error_code=status)
    code = data.get("error_code", status)
    desc = data.get("description", "unknown error")
    params = (data.get("parameters") or {}) if isinstance(data, dict) else {}
    cls = {
        401: UnauthorizedError,
        403: ForbiddenError,
        404: NotFoundError,
        429: TooManyRequestsError,
    }.get(code, TelegramAPIError)
    return cls(desc, error_code=code, description=desc, parameters=params)


def _clean(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop ``None`` values and serialize JsonMixin objects."""
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if hasattr(value, "to_dict"):
            out[key] = value.to_dict()
        elif isinstance(value, (list, tuple)):
            out[key] = [v.to_dict() if hasattr(v, "to_dict") else v for v in value]
        else:
            out[key] = value
    return out


def _require_chat_id(chat_id: int | str) -> int | str:
    if isinstance(chat_id, bool) or not isinstance(chat_id, (int, str)) or chat_id == "":
        raise ValidationError("chat_id must be a non-empty int or str")
    return chat_id


class Bot:
    """Synchronous Bot API client."""

    def __init__(
        self,
        token: str,
        *,
        base_url: str = API_BASE,
        timeout: float = 30.0,
        transport: Transport | None = None,
    ) -> None:
        if not token or not isinstance(token, str):
            raise ValidationError("token must be a non-empty string")
        self.token = token
        self.transport: Transport = transport or HttpTransport(token, base_url=base_url, timeout=timeout)

    # -- low level -----------------------------------------------------
    def call(self, method: str, **payload: Any) -> Any:
        return self.transport.request(method, _clean(payload))

    # -- core ----------------------------------------------------------
    def get_me(self) -> User:
        return User.from_dict(self.call("getMe"))  # type: ignore[return-value]

    def get_updates(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
        timeout: int | None = None,
        allowed_updates: list[str] | None = None,
    ) -> list[Update]:
        result = self.call(
            "getUpdates",
            offset=offset,
            limit=limit,
            timeout=timeout,
            allowed_updates=allowed_updates,
        )
        return [Update.from_dict(u) for u in (result or [])]  # type: ignore[misc]

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        parse_mode: str | None = None,
        message_thread_id: int | None = None,
        disable_notification: bool | None = None,
        protect_content: bool | None = None,
        reply_parameters: ReplyParameters | dict | None = None,
        reply_markup: Any = None,
        ephemeral_message_parameters: EphemeralMessageParameters | dict | None = None,
    ) -> Message:
        _require_chat_id(chat_id)
        if not isinstance(text, str) or not text:
            raise ValidationError("text must be a non-empty string")
        result = self.call(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            ephemeralMessageParameters=ephemeral_message_parameters,
        )
        return Message.from_dict(result)  # type: ignore[return-value]

    def answer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str | None = None,
        show_alert: bool | None = None,
        url: str | None = None,
        cache_time: int | None = None,
        ephemeral_message_parameters: EphemeralMessageParameters | dict | None = None,
    ) -> bool:
        if not callback_query_id:
            raise ValidationError("callback_query_id is required")
        return bool(
            self.call(
                "answerCallbackQuery",
                callbackQueryId=callback_query_id,
                text=text,
                show_alert=show_alert,
                url=url,
                cache_time=cache_time,
                ephemeralMessageParameters=ephemeral_message_parameters,
            )
        )

    # -- Bot API 10.4: widgets -----------------------------------------
    def send_widget(
        self,
        chat_id: int | str,
        html: str,
        *,
        width: int | None = None,
        height: int | None = None,
        widget_id: str | None = None,
        message_thread_id: int | None = None,
        disable_notification: bool | None = None,
        protect_content: bool | None = None,
        reply_parameters: ReplyParameters | dict | None = None,
        reply_markup: Any = None,
        ephemeral_message_parameters: EphemeralMessageParameters | dict | None = None,
    ) -> Message:
        """Send an HTML widget message (``sendWidget``)."""
        _require_chat_id(chat_id)
        validate_widget_html(html)
        validate_widget_size(width, height)
        result = self.call(
            "sendWidget",
            chat_id=chat_id,
            html=html,
            width=width,
            height=height,
            widget_id=widget_id,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            ephemeralMessageParameters=ephemeral_message_parameters,
        )
        return Message.from_dict(result)  # type: ignore[return-value]

    def send_shared_widget(
        self,
        chat_id: int | str,
        widget_id: str,
        html: str | None = None,
        *,
        width: int | None = None,
        height: int | None = None,
        message_thread_id: int | None = None,
        disable_notification: bool | None = None,
        protect_content: bool | None = None,
        reply_parameters: ReplyParameters | dict | None = None,
        reply_markup: Any = None,
        ephemeral_message_parameters: EphemeralMessageParameters | dict | None = None,
    ) -> Message:
        """Send a message reusing a shared widget (``sendSharedWidget``).

        The same ``widget_id`` can be reused across many messages;
        updating it once via :meth:`edit_shared_widget_data`
        refreshes every message that references it.
        """
        _require_chat_id(chat_id)
        if not widget_id:
            raise ValidationError("widget_id is required")
        if html is not None:
            validate_widget_html(html)
        validate_widget_size(width, height)
        result = self.call(
            "sendSharedWidget",
            chat_id=chat_id,
            widget_id=widget_id,
            html=html,
            width=width,
            height=height,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            protect_content=protect_content,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            ephemeralMessageParameters=ephemeral_message_parameters,
        )
        return Message.from_dict(result)  # type: ignore[return-value]

    def edit_message_widget_data(
        self,
        chat_id: int | str,
        message_id: int,
        data: str | dict,
        *,
        widget_id: str | None = None,
    ) -> bool:
        """Update the data of a widget in a specific message.

        (``editMessageWidgetData``)
        """
        _require_chat_id(chat_id)
        if not isinstance(message_id, int) or message_id <= 0:
            raise ValidationError("message_id must be a positive int")
        payload_data = validate_widget_data(data)
        return bool(
            self.call(
                "editMessageWidgetData",
                chat_id=chat_id,
                message_id=message_id,
                data=payload_data,
                widget_id=widget_id,
            )
        )

    def edit_shared_widget_data(self, widget_id: str, data: str | dict) -> bool:
        """Update a shared widget everywhere it is used.

        (``editSharedWidgetData``)
        """
        if not widget_id:
            raise ValidationError("widget_id is required")
        payload_data = validate_widget_data(data)
        return bool(
            self.call(
                "editSharedWidgetData",
                widget_id=widget_id,
                data=payload_data,
            )
        )

    def answer_widget_query(
        self,
        widget_query_id: str,
        *,
        text: str | None = None,
        show_alert: bool | None = None,
        cache_time: int | None = None,
        url: str | None = None,
        ephemeral_message_parameters: EphemeralMessageParameters | dict | None = None,
    ) -> bool:
        """Answer a ``WidgetQuery`` update (``answerWidgetQuery``)."""
        if not widget_query_id:
            raise ValidationError("widget_query_id is required")
        return bool(
            self.call(
                "answerWidgetQuery",
                widgetQueryId=widget_query_id,
                text=text,
                show_alert=show_alert,
                cache_time=cache_time,
                url=url,
                ephemeralMessageParameters=ephemeral_message_parameters,
            )
        )

    # -- Bot API 10.4: TON Wallet ---------------------------------------
    def get_ton_wallet_card(self, user_id: int) -> TonWalletCard:
        """Fetch public TON Wallet info for a user (``getTonWalletCard``)."""
        if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
            raise ValidationError("user_id must be a positive int")
        result = self.call("getTonWalletCard", user_id=user_id)
        return TonWalletCard.from_dict(result)  # type: ignore[return-value]

    # -- Bot API 10.4: gifts by name ------------------------------------
    def get_unique_gift(self, name: str) -> UniqueGift:
        """Look up a unique gift by name (``getUniqueGift``)."""
        if not name or not isinstance(name, str):
            raise ValidationError("name must be a non-empty string")
        result = self.call("getUniqueGift", name=name)
        return UniqueGift.from_dict(result)  # type: ignore[return-value]

    # camelCase aliases (Bot API naming) --------------------------------
    getMe = get_me
    getUpdates = get_updates
    sendMessage = send_message
    answerCallbackQuery = answer_callback_query
    sendWidget = send_widget
    sendSharedWidget = send_shared_widget
    editMessageWidgetData = edit_message_widget_data
    editSharedWidgetData = edit_shared_widget_data
    answerWidgetQuery = answer_widget_query
    getTonWalletCard = get_ton_wallet_card
    getUniqueGift = get_unique_gift
    # Friendly alias for the gift lookup.
    get_unique_gift_by_name = get_unique_gift
    getUniqueGiftByName = get_unique_gift


class AsyncBot:
    """Async wrapper around :class:`Bot` (runs blocking I/O in a thread)."""

    def __init__(self, bot: Bot | None = None, token: str | None = None, **kwargs: Any) -> None:
        if bot is not None:
            self._bot = bot
        elif token is not None:
            self._bot = Bot(token, **kwargs)
        else:
            raise ValidationError("AsyncBot requires a Bot instance or a token")

    @property
    def bot(self) -> Bot:
        return self._bot

    async def _run(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(func, *args, **kwargs)

    async def call(self, method: str, **payload: Any) -> Any:
        return await self._run(self._bot.call, method, **payload)

    async def get_me(self) -> User:
        return await self._run(self._bot.get_me)

    async def get_updates(self, **kwargs: Any) -> list[Update]:
        return await self._run(self._bot.get_updates, **kwargs)

    async def send_message(self, *args: Any, **kwargs: Any) -> Message:
        return await self._run(self._bot.send_message, *args, **kwargs)

    async def send_widget(self, *args: Any, **kwargs: Any) -> Message:
        return await self._run(self._bot.send_widget, *args, **kwargs)

    async def send_shared_widget(self, *args: Any, **kwargs: Any) -> Message:
        return await self._run(self._bot.send_shared_widget, *args, **kwargs)

    async def edit_message_widget_data(self, *args: Any, **kwargs: Any) -> bool:
        return await self._run(self._bot.edit_message_widget_data, *args, **kwargs)

    async def edit_shared_widget_data(self, *args: Any, **kwargs: Any) -> bool:
        return await self._run(self._bot.edit_shared_widget_data, *args, **kwargs)

    async def answer_widget_query(self, *args: Any, **kwargs: Any) -> bool:
        return await self._run(self._bot.answer_widget_query, *args, **kwargs)

    async def answer_callback_query(self, *args: Any, **kwargs: Any) -> bool:
        return await self._run(self._bot.answer_callback_query, *args, **kwargs)

    async def get_ton_wallet_card(self, *args: Any, **kwargs: Any) -> TonWalletCard:
        return await self._run(self._bot.get_ton_wallet_card, *args, **kwargs)

    async def get_unique_gift(self, *args: Any, **kwargs: Any) -> UniqueGift:
        return await self._run(self._bot.get_unique_gift, *args, **kwargs)

    # camelCase aliases
    sendWidget = send_widget
    sendSharedWidget = send_shared_widget
    editMessageWidgetData = edit_message_widget_data
    editSharedWidgetData = edit_shared_widget_data
    answerWidgetQuery = answer_widget_query
    getTonWalletCard = get_ton_wallet_card
    getUniqueGift = get_unique_gift
    get_unique_gift_by_name = get_unique_gift


__all__ = ["API_BASE", "AsyncBot", "Bot", "HttpTransport", "Transport"]
