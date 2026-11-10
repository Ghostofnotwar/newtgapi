import pytest

from newtgapi.types import (
    EphemeralMessageParameters,
    Message,
    ReplyParameters,
    TonWalletCard,
    TonWalletTransfer,
    UniqueGift,
    Update,
    WidgetQuery,
)


def test_widget_query_roundtrip():
    raw = {
        "id": "wq1",
        "senderChat": {"id": 42, "type": "private"},
        "chat": {"id": 42, "type": "private"},
        "message": {"messageId": 7, "chat": {"id": 42, "type": "private"}, "date": 1},
        "data": '{"action":"buy","id":1}',
        "widgetId": "shop-1",
        "queryType": "sign",
        "user": {"id": 42, "isBot": False, "firstName": "Ann"},
    }
    q = WidgetQuery.from_dict(raw)
    assert q.id == "wq1"
    assert q.query_type == "sign"
    assert q.is_ton_wallet and q.is_sign_request
    assert q.user.first_name == "Ann"
    out = q.to_dict()
    assert out["queryType"] == "sign"
    assert out["widgetId"] == "shop-1"
    assert out["senderChat"]["id"] == 42


def test_update_with_widget_query():
    upd = Update.from_dict({"updateId": 1, "widgetQuery": {"id": "x", "data": "hi"}})
    assert upd.widget_query is not None
    assert upd.widget_query.data == "hi"
    assert upd.to_dict()["widgetQuery"]["data"] == "hi"


def test_message_with_widget_and_ton_transfer():
    msg = Message.from_dict(
        {
            "messageId": 5,
            "chat": {"id": 1, "type": "private"},
            "date": 1,
            "widget": {"id": "w1", "html": "<p>hi</p>", "width": 320, "height": 240},
            "tonWalletTransfer": {
                "senderUser": {"id": 9, "firstName": "Bob"},
                "amount": 1.5,
                "comment": "thanks",
                "transactionId": "tx1",
            },
        }
    )
    assert msg.widget.width == 320
    assert msg.ton_wallet_transfer.amount == 1.5
    assert msg.ton_wallet_transfer.sender_user.first_name == "Bob"
    assert msg.to_dict()["tonWalletTransfer"]["transactionId"] == "tx1"


def test_ton_wallet_card():
    card = TonWalletCard.from_dict(
        {
            "userId": 42,
            "address": "EQ" + "A" * 46,
            "balance": 12.5,
            "balanceUsd": 30.0,
            "nftStickers": [{"stickerId": "s1", "emoji": "💎"}],
            "isConnected": True,
        }
    )
    assert card.has_balance
    assert card.nft_stickers[0].emoji == "💎"
    assert card.to_dict()["nftStickers"][0]["stickerId"] == "s1"


def test_ephemeral_requires_user_id():
    with pytest.raises(ValueError):
        EphemeralMessageParameters()
    p = EphemeralMessageParameters(user_id=7)
    assert p.to_dict() == {"userId": 7}


def test_reply_parameters_formatted_quote():
    rp = ReplyParameters(message_id=3, quote="formatted *quote*", parse_mode="MarkdownV2")
    out = rp.to_dict()
    assert out["messageId"] == 3
    assert out["quote"] == "formatted *quote*"
    assert out["parseMode"] == "MarkdownV2"


def test_unique_gift_by_name_fields():
    gift = UniqueGift.from_dict({"name": "PlushPepe", "title": "Plush Pepe", "giftId": "g1"})
    assert gift.name == "PlushPepe"
    assert gift.to_dict()["giftId"] == "g1"


def test_unknown_fields_preserved_in_extra():
    q = WidgetQuery.from_dict({"id": "1", "futureField": {"x": 1}})
    assert q.extra["futureField"] == {"x": 1}
    assert q.to_dict()["futureField"] == {"x": 1}
