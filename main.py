import asyncio
from aiogram import Bot, Dispatcher, types
from config import TOKEN, OWNER_ID
from market_checker import check_market, get_current_gifts
from keep_alive import keep_alive

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    if str(message.from_user.id) != OWNER_ID:
        await message.answer("⛔ У тебя нет доступа к этому боту.")
        return
    await message.answer("✅ Бот запущен! Я слежу за редкими подарками 🎁")

@dp.message_handler(commands=['status'])
async def status_handler(message: types.Message):
    if str(message.from_user.id) != OWNER_ID:
        return
    gifts = get_current_gifts()
    text = "🎁 Текущие цены на редкие подарки:\n"
    for g in gifts:
        text += f"• {g['name']}: {g['price']}⭐️\n"
    await message.answer(text)

async def main():
    keep_alive()
    asyncio.create_task(check_market(bot))
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())