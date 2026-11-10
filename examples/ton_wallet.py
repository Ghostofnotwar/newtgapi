"""Пример: TON Wallet (Bot API 10.4).

Запуск:  BOT_TOKEN=... python examples/ton_wallet.py
"""

import os

from newtgapi import Bot, Dispatcher
from newtgapi.ton_wallet import TonTransactionRequest, summarize_transfer, summarize_wallet_card


def main() -> None:
    bot = Bot(os.environ["BOT_TOKEN"])
    dp = Dispatcher(bot)

    @dp.on_message
    def _(b: Bot, update) -> None:
        msg = update.message
        if not msg or not msg.text:
            return
        if msg.text == "/wallet":
            card = b.get_ton_wallet_card(msg.from_user.id if msg.from_user else msg.chat.id)
            b.send_message(msg.chat.id, summarize_wallet_card(card))
        elif msg.text.startswith("/pay "):
            # /pay <TON-адрес> <сумма>
            _, address, amount = msg.text.split()
            tx = TonTransactionRequest(to=address, amount=float(amount))
            print("transaction request:", tx.to_widget_data())

    @dp.on_ton_wallet_transfer
    def _(b: Bot, update) -> None:
        transfer = update.message.ton_wallet_transfer
        b.send_message(update.message.chat.id, f"💎 {summarize_transfer(transfer)}")

    dp.poll()


if __name__ == "__main__":
    main()
