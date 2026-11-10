from newtgapi.client import Bot
from newtgapi.dispatcher import Dispatcher
from newtgapi.types import Update


class FakeTransport:
    def __init__(self):
        self.calls = []

    def request(self, method, payload):
        self.calls.append((method, payload))
        return True


def test_dispatcher_routes_widget_query_and_ton_transfer():
    bot = Bot("123:TEST", transport=FakeTransport())
    dp = Dispatcher(bot)
    seen = []

    @dp.on_widget_query
    def _(b, update):
        seen.append(("widget", update.widget_query.id))

    @dp.on_ton_wallet_transfer
    def _(b, update):
        seen.append(("ton", update.message.ton_wallet_transfer.amount))

    dp.feed(Update.from_dict({"updateId": 1, "widgetQuery": {"id": "wq1", "data": "x"}}))
    dp.feed(
        Update.from_dict(
            {
                "updateId": 2,
                "message": {
                    "messageId": 1,
                    "date": 1,
                    "chat": {"id": 1, "type": "private"},
                    "tonWalletTransfer": {"amount": 2},
                },
            }
        )
    )
    assert seen == [("widget", "wq1"), ("ton", 2)]


def test_dispatcher_poll_advances_offset():
    class PollTransport:
        def __init__(self):
            self.n = 0

        def request(self, method, payload):
            self.n += 1
            if self.n == 1:
                return [{"updateId": 10, "message": {"messageId": 1, "date": 1, "chat": {"id": 1, "type": "private"}}}]
            return []

    bot = Bot("123:TEST", transport=PollTransport())
    dp = Dispatcher(bot)
    got = []

    @dp.on_message
    def _(b, update):
        got.append(update.update_id)

    dp.poll(max_iterations=2)
    assert got == [10]
