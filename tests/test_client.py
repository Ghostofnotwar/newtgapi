import pytest

from newtgapi.client import Bot
from newtgapi.ephemeral import ephemeral_for
from newtgapi.exceptions import ValidationError
from newtgapi.types import EphemeralMessageParameters, ReplyParameters


class FakeTransport:
    def __init__(self, results=None):
        self.calls = []
        self.results = results or {}

    def request(self, method, payload):
        self.calls.append((method, payload))
        return self.results.get(method, True)


def make_bot(results=None):
    transport = FakeTransport(results)
    return Bot("123:TEST", transport=transport), transport


def test_send_widget_payload():
    bot, t = make_bot({"sendWidget": {"messageId": 1, "chat": {"id": 42, "type": "private"}, "date": 1}})
    msg = bot.send_widget(42, "<p>hi</p>", width=320, height=240)
    assert msg.message_id == 1
    method, payload = t.calls[0]
    assert method == "sendWidget"
    assert payload["chat_id"] == 42
    assert payload["html"] == "<p>hi</p>"
    assert payload["width"] == 320


def test_send_widget_validates_html():
    bot, _ = make_bot()
    with pytest.raises(ValidationError):
        bot.send_widget(42, "")


def test_send_shared_widget_and_edit_shared():
    bot, t = make_bot({"sendSharedWidget": {"messageId": 2, "date": 1}, "editSharedWidgetData": True})
    bot.send_shared_widget(42, "shop-widget", "<p>shop</p>")
    assert t.calls[0][0] == "sendSharedWidget"
    assert t.calls[0][1]["widget_id"] == "shop-widget"
    assert bot.edit_shared_widget_data("shop-widget", {"stock": 3}) is True
    assert t.calls[1][1]["data"] == '{"stock":3}'


def test_edit_message_widget_data():
    bot, t = make_bot({"editMessageWidgetData": True})
    assert bot.edit_message_widget_data(42, 7, "new-data") is True
    assert t.calls[0][1]["message_id"] == 7


def test_answer_widget_query_with_ephemeral():
    bot, t = make_bot({"answerWidgetQuery": True})
    ok = bot.answer_widget_query(
        "wq1", text="OK", ephemeral_message_parameters=ephemeral_for(99)
    )
    assert ok is True
    assert t.calls[0][1]["ephemeralMessageParameters"] == {"userId": 99}


def test_send_message_ephemeral_and_formatted_quote():
    bot, t = make_bot({"sendMessage": {"messageId": 3, "date": 1}})
    bot.send_message(
        42,
        "hello",
        reply_parameters=ReplyParameters(message_id=1, quote="q", parse_mode="HTML"),
        ephemeral_message_parameters=EphemeralMessageParameters(user_id=5),
    )
    payload = t.calls[0][1]
    assert payload["reply_parameters"]["quote"] == "q"
    assert payload["ephemeralMessageParameters"] == {"userId": 5}


def test_get_ton_wallet_card_and_unique_gift():
    bot, t = make_bot(
        {
            "getTonWalletCard": {"userId": 42, "address": "EQ" + "A" * 46, "balance": 1},
            "getUniqueGift": {"name": "PlushPepe", "title": "Plush Pepe"},
        }
    )
    card = bot.get_ton_wallet_card(42)
    assert card.balance == 1
    gift = bot.get_unique_gift("PlushPepe")
    assert gift.title == "Plush Pepe"
    assert t.calls[1][1]["name"] == "PlushPepe"


def test_camelcase_aliases():
    bot, t = make_bot({"sendWidget": {"messageId": 1, "date": 1}})
    bot.sendWidget(42, "<p>x</p>")
    assert t.calls[0][0] == "sendWidget"


def test_token_validation():
    with pytest.raises(ValidationError):
        Bot("")
