"""Minimal update dispatcher / polling loop.

Routes ``Update`` objects to handlers by type, with first-class
support for the new 10.4 update kinds: ``widget_query`` and
TON Wallet transfers (via ``Message.ton_wallet_transfer``).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Optional

from .client import AsyncBot, Bot
from .types import Update

Handler = Callable[[Any, Update], Any]
AsyncHandler = Callable[[Any, Update], Awaitable[Any]]

log = logging.getLogger(__name__)


class Dispatcher:
    """Sync dispatcher: register handlers, feed updates, or poll."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._handlers: dict[str, list[Handler]] = {}

    def on(self, update_type: str) -> Callable[[Handler], Handler]:
        """Decorator: ``@dispatcher.on("widget_query")``."""
        def decorator(func: Handler) -> Handler:
            self._handlers.setdefault(update_type, []).append(func)
            return func
        return decorator

    # Convenience registrars -------------------------------------------
    def on_message(self, func: Handler) -> Handler:
        return self.on("message")(func)

    def on_callback_query(self, func: Handler) -> Handler:
        return self.on("callback_query")(func)

    def on_widget_query(self, func: Handler) -> Handler:
        return self.on("widget_query")(func)

    def on_ton_wallet_transfer(self, func: Handler) -> Handler:
        return self.on("ton_wallet_transfer")(func)

    # Routing -----------------------------------------------------------
    def _routes_for(self, update: Update) -> list[tuple[str, Handler]]:
        routes: list[tuple[str, Handler]] = []
        if update.widget_query is not None:
            routes += [("widget_query", h) for h in self._handlers.get("widget_query", [])]
        if update.callback_query is not None:
            routes += [("callback_query", h) for h in self._handlers.get("callback_query", [])]
        if update.message is not None:
            routes += [("message", h) for h in self._handlers.get("message", [])]
            if update.message.ton_wallet_transfer is not None:
                routes += [
                    ("ton_wallet_transfer", h)
                    for h in self._handlers.get("ton_wallet_transfer", [])
                ]
        return routes

    def feed(self, update: Update) -> None:
        for _kind, handler in self._routes_for(update):
            try:
                handler(self.bot, update)
            except Exception:  # noqa: BLE001 - keep polling alive
                log.exception("handler %r failed for update %s", handler, update.update_id)

    def feed_many(self, updates: list[Update]) -> None:
        for update in updates:
            self.feed(update)

    def poll(
        self,
        *,
        timeout: int = 30,
        limit: int = 100,
        allowed_updates: list[str] | None = None,
        max_iterations: int | None = None,
    ) -> None:
        """Blocking long-poll loop (``getUpdates``)."""
        offset: Optional[int] = None
        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            iteration += 1
            updates = self.bot.get_updates(
                offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates
            )
            for update in updates:
                self.feed(update)
                if update.update_id is not None:
                    offset = update.update_id + 1


class AsyncDispatcher(Dispatcher):
    """Async dispatcher for :class:`AsyncBot`."""

    def __init__(self, bot: AsyncBot) -> None:
        # Keep the sync base init from touching the bot type.
        self.bot = bot  # type: ignore[assignment]
        self._handlers: dict[str, list[Any]] = {}

    async def feed_async(self, update: Update) -> None:
        for _kind, handler in self._routes_for(update):
            try:
                result = handler(self.bot, update)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:  # noqa: BLE001
                log.exception("handler %r failed for update %s", handler, update.update_id)

    async def poll_async(
        self,
        *,
        timeout: int = 30,
        limit: int = 100,
        allowed_updates: list[str] | None = None,
        max_iterations: int | None = None,
    ) -> None:
        offset: Optional[int] = None
        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            iteration += 1
            updates = await self.bot.get_updates(
                offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates
            )
            for update in updates:
                await self.feed_async(update)
                if update.update_id is not None:
                    offset = update.update_id + 1


__all__ = ["AsyncDispatcher", "Dispatcher"]
