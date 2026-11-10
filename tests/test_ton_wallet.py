import pytest

from newtgapi.exceptions import ValidationError
from newtgapi.ton_wallet import (
    TonSignRequest,
    TonTransactionRequest,
    format_ton_amount,
    is_valid_ton_address,
    summarize_transfer,
    summarize_wallet_card,
)
from newtgapi.types import TonWalletCard, TonWalletTransfer, User

VALID = "EQ" + "A" * 46  # 48 chars


def test_address_validation():
    assert is_valid_ton_address(VALID)
    assert is_valid_ton_address("0:" + "ab" * 32)
    assert not is_valid_ton_address("short")
    assert not is_valid_ton_address("")


def test_format_amount():
    assert format_ton_amount(1.5) == "1.5"
    assert format_ton_amount(2) == "2"
    assert format_ton_amount(0.000000001) == "0.000000001"
    with pytest.raises(ValidationError):
        format_ton_amount(-1)


def test_sign_request_roundtrip():
    req = TonSignRequest(payload="hello", text="Sign this")
    back = TonSignRequest.from_widget_data(req.to_widget_data())
    assert back.payload == "hello"
    assert back.text == "Sign this"


def test_transaction_request_validates():
    tx = TonTransactionRequest(to=VALID, amount=0.5, comment="pay")
    assert tx.amount == 0.5
    with pytest.raises(ValidationError):
        TonTransactionRequest(to="bad", amount=1)
    with pytest.raises(ValidationError):
        TonTransactionRequest(to=VALID, amount=0)


def test_summaries():
    card = TonWalletCard(user_id=1, address=VALID, balance=3, nft_stickers=[])
    assert "3 TON" in summarize_wallet_card(card)
    transfer = TonWalletTransfer(amount=1, sender_user=User(id=2, first_name="Bob"), comment="hi")
    assert "Bob" in summarize_transfer(transfer)
