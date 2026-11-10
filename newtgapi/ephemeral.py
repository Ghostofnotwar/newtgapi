"""Ephemeral (per-user) message helpers (Bot API 10.4).

Button and widget presses in group chats can be answered with a
message visible only to the user who pressed.  Pass
:class:`~newtgapi.types.EphemeralMessageParameters` to
``send_message`` / ``answer_callback_query`` / ``answer_widget_query``.
"""

from __future__ import annotations

from .exceptions import ValidationError
from .types import EphemeralMessageParameters


def ephemeral_for(user_id: int, *, message_thread_id: int | None = None) -> EphemeralMessageParameters:
    """Shorthand constructor with validation."""
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise ValidationError("user_id must be a positive int")
    return EphemeralMessageParameters(user_id=user_id, message_thread_id=message_thread_id)


def ephemeral_from_callback(callback_query: object) -> EphemeralMessageParameters:
    """Build ephemeral params from a ``CallbackQuery`` (its ``from_user``)."""
    from_user = getattr(callback_query, "from_user", None)
    user_id = getattr(from_user, "id", None) if from_user else None
    if user_id is None:
        raise ValidationError("callback_query has no from_user.id")
    return ephemeral_for(user_id)


def ephemeral_from_widget_query(widget_query: object) -> EphemeralMessageParameters:
    """Build ephemeral params from a ``WidgetQuery``."""
    user = getattr(widget_query, "user", None)
    user_id = getattr(user, "id", None) if user else None
    if user_id is None:
        sender = getattr(widget_query, "sender_chat", None)
        user_id = getattr(sender, "id", None) if sender else None
    if user_id is None:
        raise ValidationError("widget_query has no user/sender_chat id")
    return ephemeral_for(user_id)


__all__ = ["ephemeral_for", "ephemeral_from_callback", "ephemeral_from_widget_query"]
