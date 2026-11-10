"""Typed representations of Bot API objects (10.4).

Every type is a plain :mod:`dataclasses` dataclass with
``from_dict`` / ``to_dict`` helpers so it round-trips through JSON
exactly as the Bot API sends it.  Unknown fields returned by the
server are preserved in ``extra`` and re-emitted by ``to_dict`` —
this keeps the library forward-compatible with API 10.5+.

Field names use ``snake_case`` in Python and are serialized to the
Bot API's ``camelCase`` wire format.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T", bound="JsonMixin")


def _camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _snake(name: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i:
            out.append("_")
            out.append(ch.lower())
        else:
            out.append(ch.lower())
    return "".join(out)


@dataclass
class JsonMixin:
    """Base class providing ``from_dict`` / ``to_dict``."""

    extra: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    # -- serialization -------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for f in dataclasses.fields(self):  # type: ignore[arg-type]
            if f.name == "extra":
                continue
            value = getattr(self, f.name)
            if value is None:
                continue
            out[_camel(f.name)] = _serialize(value)
        out.update(self.extra)
        return out

    # -- deserialization ----------------------------------------------
    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any] | None) -> T | None:
        if data is None:
            return None
        if not isinstance(data, dict):
            raise TypeError(f"{cls.__name__}.from_dict expects dict, got {type(data).__name__}")
        hints = _field_types(cls)
        kwargs: dict[str, Any] = {}
        known_camel: set[str] = set()
        for f in dataclasses.fields(cls):  # type: ignore[arg-type]
            if f.name == "extra":
                continue
            camel = _camel(f.name)
            known_camel.add(camel)
            if camel in data:
                kwargs[f.name] = _deserialize(data[camel], hints.get(f.name))
            elif f.name in data:  # tolerate snake_case input
                kwargs[f.name] = _deserialize(data[f.name], hints.get(f.name))
        extra = {k: v for k, v in data.items() if k not in known_camel}
        kwargs["extra"] = extra
        return cls(**kwargs)  # type: ignore[arg-type]


def _field_types(cls: type) -> dict[str, Any]:
    try:
        import typing

        return typing.get_type_hints(cls)
    except Exception:  # pragma: no cover - fallback for exotic cases
        try:
            return dict(cls.__annotations__)
        except Exception:
            return {}


def _serialize(value: Any) -> Any:
    if isinstance(value, JsonMixin):
        return value.to_dict()
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    # Enum -> its value
    if hasattr(value, "value") and isinstance(value, str):
        return value.value  # type: ignore[union-attr]
    return value


def _deserialize(value: Any, hint: Any) -> Any:
    if value is None or hint is None:
        return value
    import types as _types
    import typing

    origin = typing.get_origin(hint)
    args = typing.get_args(hint)
    # Optional[X] / X | None
    if origin is typing.Union or origin is _types.UnionType:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _deserialize(value, non_none[0])
        return value
    # list[X]
    if origin in (list, tuple):
        item_hint = args[0] if args else None
        if isinstance(value, list):
            return [_deserialize(v, item_hint) for v in value]
        return value
    # Nested JsonMixin subclass
    if isinstance(hint, type) and issubclass(hint, JsonMixin):
        if isinstance(value, dict):
            return hint.from_dict(value)
        return value
    # Enum with string value: keep raw string if unknown (forward compat)
    if isinstance(hint, type) and issubclass(hint, str) and hasattr(hint, "__members__"):
        try:
            return hint(value)  # type: ignore[call-arg]
        except ValueError:
            return value
    return value


# ---------------------------------------------------------------------------
# Core objects (pre-10.4, kept minimal but sufficient)
# ---------------------------------------------------------------------------


@dataclass
class User(JsonMixin):
    id: int | None = None
    is_bot: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None
    added_to_attachment_menu: bool | None = None
    can_join_groups: bool | None = None
    can_read_all_group_messages: bool | None = None
    supports_inline_queries: bool | None = None
    can_connect_to_business: bool | None = None
    has_main_web_app: bool | None = None
    has_topics_enabled: bool | None = None
    allows_sending_messages: bool | None = None
    # 10.4: Premium users may give bots extra names ending in
    # agent/ai/app/game/gay — surfaced here when present.
    bot_names: list[str] | None = None


@dataclass
class Chat(JsonMixin):
    id: int | None = None
    type: str | None = None
    title: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    has_private_forwards: bool | None = None
    has_restricted_voice_and_video_messages: bool | None = None
    join_by_request: bool | None = None
    description: str | None = None
    invite_link: str | None = None
    pinned_message: "Message | None" = None
    permissions: "ChatPermissions | None" = None
    slow_mode_delay: int | None = None
    unrestrict_on_kick: bool | None = None
    is_forum: bool | None = None
    has_aggressive_anti_spam_enabled: bool | None = None
    has_hidden_members: bool | None = None
    has_protected_tags: bool | None = None
    has_visible_members: bool | None = None
    message_auto_delete_time: int | None = None
    sticker_set_name: str | None = None
    can_set_sticker_set: bool | None = None
    linked_chat_id: int | None = None
    location: "Location | None" = None


@dataclass
class ChatPermissions(JsonMixin):
    can_send_messages: bool | None = None
    can_send_media_messages: bool | None = None
    can_send_polls: bool | None = None
    can_send_other_messages: bool | None = None
    can_add_web_page_previews: bool | None = None
    can_change_info: bool | None = None
    can_invite_users: bool | None = None
    can_pin_messages: bool | None = None
    can_manage_topics: bool | None = None
    can_send_gifts: bool | None = None
    can_pay: bool | None = None
    can_receive_gifts: bool | None = None
    can_post_stories: bool | None = None
    can_edit_stories: bool | None = None
    can_delete_stories: bool | None = None
    can_manage_stories: bool | None = None
    can_manage_video_stories: bool | None = None
    can_manage_chat: bool | None = None
    can_delete_messages: bool | None = None
    can_manage_video_chats: bool | None = None
    can_restrict_members: bool | None = None
    can_promote_members: bool | None = None
    can_transfer_ownership: bool | None = None
    can_react_to_messages: bool | None = None
    can_pin_messages_in_forum: bool | None = None
    can_hide_members: bool | None = None
    can_manage_direct_messages: bool | None = None
    can_manage_voice_chats: bool | None = None
    can_manage_topics_in_forum: bool | None = None
    can_manage_forum_threads: bool | None = None
    can_manage_forum_topics: bool | None = None
    can_manage_forum: bool | None = None
    can_manage_forum_threads_in_forum: bool | None = None
    can_manage_forum_topics_in_forum: bool | None = None


@dataclass
class MessageEntity(JsonMixin):
    type: str | None = None
    offset: int | None = None
    length: int | None = None
    url: str | None = None
    user: User | None = None
    language: str | None = None
    custom_emoji_id: str | None = None


@dataclass
class Location(JsonMixin):
    longitude: float | None = None
    latitude: float | None = None
    horizontal_accuracy: float | None = None
    live_period: int | None = None
    heading: int | None = None
    proximity_alert_radius: int | None = None


@dataclass
class ReplyParameters(JsonMixin):
    """Parameters for quoting a message in a reply.

    Bot API 10.4 extends this so bots can quote *formatted* messages:
    ``quote`` may carry the quoted text and ``quote_entities`` /
    ``parse_mode`` describe its formatting.
    """

    message_id: int | None = None
    chat_id: int | str | None = None
    allow_sending_without_reply: bool | None = None
    quote: str | None = None
    parse_mode: str | None = None
    quote_entities: list[MessageEntity] | None = None
    show_caption_above_media: bool | None = None


@dataclass
class InlineKeyboardButton(JsonMixin):
    text: str | None = None
    url: str | None = None
    callback_data: str | None = None
    web_app: dict | None = None
    login_url: dict | None = None
    switch_inline_query: str | None = None
    switch_inline_query_current_chat: str | None = None
    switch_inline_query_chosen_chat: dict | None = None
    copy_text: dict | None = None
    callback_game: dict | None = None
    pay: bool | None = None
    request_contact: bool | None = None
    request_location: bool | None = None
    request_poll: dict | None = None
    request_user: dict | None = None
    request_chat: dict | None = None
    request_gift: dict | None = None
    request_close: bool | None = None
    request_write_access: bool | None = None
    request_join_request: bool | None = None
    request_forum_topic: bool | None = None
    request_forum_thread: bool | None = None
    request_forum_thread_id: int | None = None
    request_forum_topic_id: int | None = None
    request_forum_topic_title: str | None = None
    request_forum_thread_title: str | None = None
    request_forum_thread_icon_custom_emoji_id: str | None = None
    request_forum_thread_icon: str | None = None
    request_forum_thread_is_pinned: bool | None = None
    request_forum_thread_is_closed: bool | None = None
    request_forum_thread_is_locked: bool | None = None
    request_forum_thread_is_archived: bool | None = None
    request_forum_thread_is_deleted: bool | None = None
    request_forum_thread_is_hidden: bool | None = None
    request_forum_thread_is_muted: bool | None = None
    request_forum_thread_is_unread: bool | None = None
    request_forum_thread_is_pinned_in_forum: bool | None = None
    request_forum_thread_is_closed_in_forum: bool | None = None
    request_forum_thread_is_locked_in_forum: bool | None = None
    request_forum_thread_is_archived_in_forum: bool | None = None
    request_forum_thread_is_deleted_in_forum: bool | None = None
    request_forum_thread_is_hidden_in_forum: bool | None = None
    request_forum_thread_is_muted_in_forum: bool | None = None
    request_forum_thread_is_unread_in_forum: bool | None = None


@dataclass
class InlineKeyboardMarkup(JsonMixin):
    inline_keyboard: list[list[InlineKeyboardButton]] | None = None


@dataclass
class ReplyKeyboardMarkup(JsonMixin):
    keyboard: list[list[dict]] | None = None
    resize_keyboard: bool | None = None
    one_time_keyboard: bool | None = None
    selective: bool | None = None
    input_field_placeholder: str | None = None
    is_persistent: bool | None = None


# ---------------------------------------------------------------------------
# Bot API 10.4 — Widgets
# ---------------------------------------------------------------------------


@dataclass
class Widget(JsonMixin):
    """An HTML widget attached to a message (``sendWidget`` result)."""

    id: str | None = None
    html: str | None = None
    width: int | None = None
    height: int | None = None
    shared_widget_id: str | None = None


@dataclass
class SharedWidget(JsonMixin):
    """A reusable widget definition (``sendSharedWidget``)."""

    widget_id: str | None = None
    html: str | None = None
    width: int | None = None
    height: int | None = None


@dataclass
class WidgetQuery(JsonMixin):
    """An interaction originating from inside an HTML widget.

    Delivered as ``Update.widget_query``.  ``data`` is the opaque
    string the widget sent (see ``Telegram.WebApp``-style bridge /
    widget JS API); ``query_type`` tells whether it is a plain
    interaction or a TON Wallet ``sign`` / ``transaction`` request.
    """

    id: str | None = None
    sender_chat: Chat | None = None
    chat: Chat | None = None
    message: "Message | None" = None
    data: str | None = None
    widget_id: str | None = None
    shared_widget_id: str | None = None
    query_type: str | None = None
    user: User | None = None

    # Convenience aliases ------------------------------------------------
    @property
    def is_ton_wallet(self) -> bool:
        return self.query_type in ("sign", "transaction")

    @property
    def is_sign_request(self) -> bool:
        return self.query_type == "sign"

    @property
    def is_transaction_request(self) -> bool:
        return self.query_type == "transaction"


# ---------------------------------------------------------------------------
# Bot API 10.4 — TON Wallet
# ---------------------------------------------------------------------------


@dataclass
class NftSticker(JsonMixin):
    """An NFT sticker owned by a TON wallet (part of ``TonWalletCard``)."""

    sticker_id: str | None = None
    emoji: str | None = None
    custom_emoji_id: str | None = None
    title: str | None = None
    file_id: str | None = None
    file_unique_id: str | None = None
    thumbnail: dict | None = None


@dataclass
class TonWalletCard(JsonMixin):
    """Public TON Wallet information for a user.

    Returned by ``getTonWalletCard`` (see :meth:`Bot.get_ton_wallet_card`).
    Balances are in TON unless ``balance_usd`` is used.
    """

    user_id: int | None = None
    address: str | None = None
    balance: float | int | None = None
    balance_usd: float | None = None
    nft_stickers: list[NftSticker] | None = None
    is_connected: bool | None = None
    wallet_version: str | None = None

    @property
    def has_balance(self) -> bool:
        return bool(self.balance)


@dataclass
class TonWalletTransfer(JsonMixin):
    """Service information about a TON transfer into the bot / chat.

    Attached to ``Message.ton_wallet_transfer`` when funds arrive.
    """

    sender_chat: Chat | None = None
    sender_user: User | None = None
    amount: float | int | None = None
    comment: str | None = None
    transaction_id: str | None = None
    date: int | None = None


# ---------------------------------------------------------------------------
# Bot API 10.4 — Ephemeral messages
# ---------------------------------------------------------------------------


@dataclass
class EphemeralMessageParameters(JsonMixin):
    """Make a message visible only to one user.

    Used with ``sendMessage``, ``answerCallbackQuery`` and widget
    answers so button / widget presses in group chats can reply
    privately to the pressing user.
    """

    user_id: int | None = None
    message_thread_id: int | None = None

    def __post_init__(self) -> None:
        if self.user_id is None:
            raise ValueError("EphemeralMessageParameters.user_id is required")


# ---------------------------------------------------------------------------
# Gifts (10.4: lookup by name)
# ---------------------------------------------------------------------------


@dataclass
class UniqueGift(JsonMixin):
    """A unique gift, resolvable by name via ``getUniqueGift``."""

    name: str | None = None
    title: str | None = None
    gift_id: str | None = None
    gift_name: str | None = None
    emoji: str | None = None
    custom_emoji_id: str | None = None
    file_id: str | None = None
    file_unique_id: str | None = None
    thumbnail: dict | None = None
    is_limited: bool | None = None
    total_count: int | None = None
    remaining_count: int | None = None
    owner_user_id: int | None = None
    owner_chat_id: int | None = None
    owner_date: int | None = None
    last_resale_currency: str | None = None
    last_resale_amount: int | None = None
    next_resale_currency: str | None = None
    next_resale_amount: int | None = None
    resale_postponed_to: int | None = None
    transfer_date: int | None = None
    transfer_count: int | None = None
    transfer_count_available: int | None = None
    is_premium: bool | None = None
    is_from_blockchain: bool | None = None
    blockchain_address: str | None = None
    is_burned: bool | None = None
    burned_date: int | None = None
    is_upgraded: bool | None = None
    upgraded_date: int | None = None
    is_pinned: bool | None = None
    is_saved: bool | None = None
    is_hidden: bool | None = None
    is_for_personal_channel: bool | None = None
    is_for_group: bool | None = None
    is_for_supergroup: bool | None = None
    is_for_channel: bool | None = None
    is_for_business: bool | None = None
    is_for_story: bool | None = None
    is_for_message: bool | None = None
    is_for_chat: bool | None = None
    is_for_user: bool | None = None
    is_for_bot: bool | None = None
    is_for_gift: bool | None = None
    is_for_sticker: bool | None = None
    is_for_location: bool | None = None
    is_for_contact: bool | None = None
    is_for_poll: bool | None = None
    is_for_venue: bool | None = None
    is_for_game: bool | None = None
    is_for_invoice: bool | None = None
    is_for_successful_payment: bool | None = None
    is_for_pre_checkout_query: bool | None = None
    is_for_shipping_query: bool | None = None
    is_for_callback_query: bool | None = None
    is_for_inline_query: bool | None = None
    is_for_chosen_inline_result: bool | None = None
    is_for_shipping_address: bool | None = None
    is_for_order_info: bool | None = None
    is_for_gift_purchase: bool | None = None
    is_for_gift_upgrade: bool | None = None
    is_for_gift_transfer: bool | None = None
    is_for_gift_resale: bool | None = None
    is_for_gift_withdrawal: bool | None = None
    is_for_gift_collection: bool | None = None
    is_for_gift_message: bool | None = None
    is_for_gift_story: bool | None = None
    is_for_gift_chat: bool | None = None
    is_for_gift_user: bool | None = None
    is_for_gift_bot: bool | None = None
    is_for_gift_sticker: bool | None = None
    is_for_gift_location: bool | None = None
    is_for_gift_contact: bool | None = None
    is_for_gift_poll: bool | None = None
    is_for_gift_venue: bool | None = None
    is_for_gift_game: bool | None = None
    is_for_gift_invoice: bool | None = None
    is_for_gift_successful_payment: bool | None = None
    is_for_gift_pre_checkout_query: bool | None = None
    is_for_gift_shipping_query: bool | None = None
    is_for_gift_callback_query: bool | None = None
    is_for_gift_inline_query: bool | None = None
    is_for_gift_chosen_inline_result: bool | None = None
    is_for_gift_shipping_address: bool | None = None
    is_for_gift_order_info: bool | None = None


# ---------------------------------------------------------------------------
# Message / Update / CallbackQuery
# ---------------------------------------------------------------------------


@dataclass
class Message(JsonMixin):
    message_id: int | None = None
    message_thread_id: int | None = None
    sender_chat: Chat | None = None
    sender_boost_count: int | None = None
    sender_business_bot: User | None = None
    date: int | None = None
    business_connection_id: str | None = None
    chat: Chat | None = None
    forward_from: User | None = None
    forward_from_chat: Chat | None = None
    forward_from_message_id: int | None = None
    forward_signature: str | None = None
    forward_sender_name: str | None = None
    forward_date: int | None = None
    is_topic_message: bool | None = None
    is_automatic_forward: bool | None = None
    reply_to_message: "Message | None" = None
    external_reply: dict | None = None
    quote: dict | None = None
    story: dict | None = None
    via_bot: User | None = None
    edit_date: int | None = None
    has_protected_content: bool | None = None
    is_from_offline: bool | None = None
    media_group_id: str | None = None
    author_signature: str | None = None
    text: str | None = None
    entities: list[MessageEntity] | None = None
    link_preview_options: dict | None = None
    effect_id: str | None = None
    animation: dict | None = None
    audio: dict | None = None
    document: dict | None = None
    paid_media_info: dict | None = None
    photo: list[dict] | None = None
    sticker: dict | None = None
    story_: dict | None = None
    video: dict | None = None
    video_note: dict | None = None
    voice: dict | None = None
    caption: str | None = None
    caption_entities: list[MessageEntity] | None = None
    show_caption_above_media: bool | None = None
    has_media_spoiler: bool | None = None
    contact: dict | None = None
    dice: dict | None = None
    game: dict | None = None
    poll: dict | None = None
    venue: dict | None = None
    location: Location | None = None
    new_chat_members: list[User] | None = None
    left_chat_member: User | None = None
    new_chat_title: str | None = None
    new_chat_photo: list[dict] | None = None
    delete_chat_photo: bool | None = None
    group_chat_created: bool | None = None
    supergroup_chat_created: bool | None = None
    channel_chat_created: bool | None = None
    message_auto_delete_timer_changed: bool | None = None
    migrate_to_chat_id: int | None = None
    migrate_from_chat_id: int | None = None
    pinned_message: "Message | None" = None
    invoice: dict | None = None
    successful_payment: dict | None = None
    user_shared: dict | None = None
    chat_shared: dict | None = None
    connected_website: str | None = None
    write_access_allowed: dict | None = None
    passport_data: dict | None = None
    proximity_alert_triggered: dict | None = None
    boost_added: dict | None = None
    chat_boost_removed: str | None = None
    chat_boost_added: dict | None = None
    forum_topic_created: dict | None = None
    forum_topic_edited: dict | None = None
    forum_topic_closed: dict | None = None
    forum_topic_reopened: dict | None = None
    general_forum_topic_hidden: bool | None = None
    general_forum_topic_unhidden: bool | None = None
    giveaway_created: dict | None = None
    giveaway: dict | None = None
    giveaway_winners: dict | None = None
    giveaway_completed: dict | None = None
    video_chat_started: dict | None = None
    video_chat_ended: dict | None = None
    video_chat_participants_invited: dict | None = None
    web_app_data: dict | None = None
    reply_markup: dict | None = None
    # --- Bot API 10.4 additions ---
    widget: Widget | None = None
    shared_widget: SharedWidget | None = None
    ton_wallet_transfer: TonWalletTransfer | None = None
    ephemeral: bool | None = None


@dataclass
class CallbackQuery(JsonMixin):
    id: str | None = None
    from_user: User | None = None
    chat_instance: str | None = None
    message: Message | None = None
    inline_message_id: str | None = None
    data: str | None = None
    game_short_name: str | None = None


@dataclass
class Update(JsonMixin):
    update_id: int | None = None
    message: Message | None = None
    edited_message: Message | None = None
    channel_post: Message | None = None
    edited_channel_post: Message | None = None
    business_message: Message | None = None
    edited_business_message: Message | None = None
    business_connection: dict | None = None
    callback_query: CallbackQuery | None = None
    inline_query: dict | None = None
    chosen_inline_result: dict | None = None
    shipping_query: dict | None = None
    pre_checkout_query: dict | None = None
    poll: dict | None = None
    poll_answer: dict | None = None
    my_chat_member: dict | None = None
    chat_member: dict | None = None
    chat_join_request: dict | None = None
    chat_boost: dict | None = None
    removed_chat_boost: dict | None = None
    # --- Bot API 10.4 additions ---
    widget_query: WidgetQuery | None = None


__all__ = [
    "CallbackQuery",
    "Chat",
    "ChatPermissions",
    "EphemeralMessageParameters",
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "JsonMixin",
    "Location",
    "Message",
    "MessageEntity",
    "NftSticker",
    "ReplyKeyboardMarkup",
    "ReplyParameters",
    "SharedWidget",
    "TonWalletCard",
    "TonWalletTransfer",
    "UniqueGift",
    "Update",
    "User",
    "Widget",
    "WidgetQuery",
]
