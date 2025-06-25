import asyncio
import json
import os
from config import OWNER_ID

GIFTS = [
    {"name": "Пасхальное яйцо", "id": "egg", "price": 1059},
    {"name": "Коробка-сюрприз", "id": "surprise", "price": 994},
    {"name": "Кошачий шлем", "id": "cat_helmet", "price": 13950},
    {"name": "Шлем воина", "id": "warrior_helmet", "price": 20999},
    {"name": "Цилиндр", "id": "hat", "price": 3699},
    {"name": "Бант", "id": "bow", "price": 1800},
    {"name": "Световой меч", "id": "saber", "price": 1250},
    {"name": "Кольцо", "id": "ring", "price": 33333},
    {"name": "Обручальное кольцо", "id": "engaged", "price": 59999},
    {"name": "Зелье любви", "id": "potion", "price": 3750},
    {"name": "Мишка", "id": "bear", "price": 7000},
    {"name": "Кейс с кольцом", "id": "case", "price": 6666}
]

DATA_FILE = "data.json"

def get_current_gifts():
    return GIFTS

async def check_market(bot):
    await asyncio.sleep(2)
    while True:
        old_data = {}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                old_data = json.load(f)

        new_data = {}
        for gift in GIFTS:
            gift_id = gift["id"]
            gift_price = gift["price"]
            new_data[gift_id] = gift_price
            old_price = old_data.get(gift_id)

            if old_price is None:
                await bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"🆕 Новый подарок: {gift['name']} — {gift_price}⭐️"
                )
            elif old_price != gift_price:
                await bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"🔄 {gift['name']} изменилась цена: была {old_price}⭐️, стала {gift_price}⭐️"
                )

        with open(DATA_FILE, "w") as f:
            json.dump(new_data, f, indent=2)

        await asyncio.sleep(1800)