"""TON Wallet helpers (Bot API 10.4).

Widgets can request a signature or a transaction confirmation from
the user's native TON Wallet.  This module keeps the wallet-specific
logic (payload building, address validation, transfer formatting)
in one place so bot code stays readable.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass

from .exceptions import ValidationError
from .types import TonWalletCard, TonWalletTransfer

# TON user-friendly address: 48 chars, base64url-ish alphabet.
_TON_ADDRESS_RE = re.compile(r"^[A-Za-z0-9_\-]{48}$")
# Raw address: <workchain>:<64 hex>
_TON_RAW_RE = re.compile(r"^-?\d:[0-9a-fA-F]{64}$")


def is_valid_ton_address(address: str) -> bool:
    return bool(_TON_ADDRESS_RE.match(address) or _TON_RAW_RE.match(address))


def validate_ton_address(address: str) -> str:
    if not isinstance(address, str) or not is_valid_ton_address(address.strip()):
        raise ValidationError(f"invalid TON address: {address!r}")
    return address.strip()


def format_ton_amount(amount: float | int) -> str:
    """Format a TON amount for display (trims trailing zeros)."""
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValidationError("amount must be a number")
    if amount < 0:
        raise ValidationError("amount must be non-negative")
    text = f"{amount:.9f}".rstrip("0").rstrip(".")
    return text or "0"


@dataclass
class TonSignRequest:
    """Payload for a ``sign`` widget query."""

    payload: str
    text: str | None = None

    def to_widget_data(self) -> str:
        return json.dumps(
            {"type": "sign", "payload": self.payload, "text": self.text},
            ensure_ascii=False,
        )

    @classmethod
    def from_widget_data(cls, data: str | dict) -> "TonSignRequest":
        if isinstance(data, str):
            data = json.loads(data)
        return cls(payload=data.get("payload", ""), text=data.get("text"))


@dataclass
class TonTransactionRequest:
    """Payload for a ``transaction`` widget query."""

    to: str
    amount: float | int
    comment: str | None = None
    state_init: str | None = None

    def __post_init__(self) -> None:
        validate_ton_address(self.to)
        if not isinstance(self.amount, (int, float)) or self.amount <= 0:
            raise ValidationError("transaction amount must be positive")

    def to_widget_data(self) -> str:
        return json.dumps(
            {
                "type": "transaction",
                "to": self.to,
                "amount": self.amount,
                "comment": self.comment,
                "stateInit": self.state_init,
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_widget_data(cls, data: str | dict) -> "TonTransactionRequest":
        if isinstance(data, str):
            data = json.loads(data)
        return cls(
            to=data.get("to", ""),
            amount=data.get("amount", 0),
            comment=data.get("comment"),
            state_init=data.get("stateInit"),
        )


def summarize_wallet_card(card: TonWalletCard) -> str:
    """One-line human summary of a wallet card (for logs / messages)."""
    balance = format_ton_amount(card.balance) if card.balance is not None else "?"
    nft_count = len(card.nft_stickers or [])
    return f"TON {card.address} — balance {balance} TON, NFT stickers: {nft_count}"


def summarize_transfer(transfer: TonWalletTransfer) -> str:
    amount = format_ton_amount(transfer.amount) if transfer.amount is not None else "?"
    sender = (
        (transfer.sender_user.first_name if transfer.sender_user else None)
        or (transfer.sender_user.username if transfer.sender_user else None)
        or (transfer.sender_chat.title if transfer.sender_chat else None)
        or "unknown"
    )
    comment = f" ({transfer.comment})" if transfer.comment else ""
    return f"Received {amount} TON from {sender}{comment}"


def encode_state_init(state_init: str) -> str:
    """Validate that ``state_init`` looks like base64 (BOC) data."""
    try:
        base64.b64decode(state_init, validate=True)
    except Exception as exc:
        raise ValidationError("state_init must be valid base64") from exc
    return state_init


__all__ = [
    "TonSignRequest",
    "TonTransactionRequest",
    "encode_state_init",
    "format_ton_amount",
    "is_valid_ton_address",
    "summarize_transfer",
    "summarize_wallet_card",
    "validate_ton_address",
]
