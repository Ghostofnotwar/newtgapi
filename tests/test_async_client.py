import pytest

from newtgapi.client import AsyncBot, Bot


class FakeTransport:
    def request(self, method, payload):
        if method == "sendWidget":
            return {"messageId": 9, "date": 1}
        return True


@pytest.mark.asyncio
async def test_async_send_widget():
    bot = AsyncBot(Bot("123:TEST", transport=FakeTransport()))
    msg = await bot.send_widget(42, "<p>async</p>")
    assert msg.message_id == 9
