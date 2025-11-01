import asyncio
import json
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.payments import GetStarGiftsRequest

# ====== НАЛАШТУВАННЯ ======
# Отримай новий токен через @BotFather командою /newbot або /token
BOT_TOKEN = os.getenv('BOT_TOKEN', '7485544169:AAGlnhXW44T8haR2tYeBBXZqdeZvXwpylrs')
API_ID = int(os.getenv('API_ID', '25251147'))
API_HASH = os.getenv('API_HASH', '616c6d1719f3944a7d179238e58cc9c8')
PHONE = os.getenv('PHONE', '+14343874582')
USER_ID = int(os.getenv('USER_ID', '7841825969'))  # Твій User ID
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))  # 5 хвилин

# Файл для збереження відомих подарунків
DATA_FILE = 'known_gifts.json'

# ====== КОД БОТА ======

def load_known_gifts():
    """Завантажує список відомих подарунків"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_known_gifts(gifts_data):
    """Зберігає список відомих подарунків"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(gifts_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Помилка збереження: {e}")

def get_gift_name(sticker):
    """Отримує ім'я подарунка зі стікера"""
    if not sticker or not hasattr(sticker, 'attributes'):
        return None
    
    for attr in sticker.attributes:
        if hasattr(attr, 'alt') and attr.alt:
            return attr.alt
    return None

async def get_available_gifts(client):
    """Отримує список доступних подарунків з retry логікою"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Перевіряємо з'єднання
            if not client.is_connected():
                print(f"🔄 Перепідключення... (спроба {attempt + 1}/{max_retries})")
                await client.connect()
            
            result = await client(GetStarGiftsRequest(hash=0))
            gifts = {}
            
            for gift in result.gifts:
                gift_id = gift.id
                
                # Отримуємо інформацію про стікер
                sticker_emoji = None
                if hasattr(gift, 'sticker') and gift.sticker:
                    if hasattr(gift.sticker, 'attributes'):
                        for attr in gift.sticker.attributes:
                            attr_type = type(attr).__name__
                            if 'CustomEmoji' in attr_type or 'Sticker' in attr_type:
                                if hasattr(attr, 'alt') and attr.alt:
                                    sticker_emoji = attr.alt
                                    break
                
                gifts[gift_id] = {
                    'id': gift_id,
                    'emoji': sticker_emoji,
                    'stars': gift.stars,
                    'convert_stars': getattr(gift, 'convert_stars', None),
                    'limited': getattr(gift, 'limited', False),
                    'sold_out': getattr(gift, 'sold_out', False),
                    'birthday': getattr(gift, 'birthday', False),
                    'require_premium': getattr(gift, 'require_premium', False),
                    'availability_remains': getattr(gift, 'availability_remains', None),
                    'availability_total': getattr(gift, 'availability_total', None),
                    'per_user_remains': getattr(gift, 'per_user_remains', None),
                    'per_user_total': getattr(gift, 'per_user_total', None),
                }
            
            return gifts
            
        except (ConnectionError, OSError) as e:
            print(f"⚠️ Помилка з'єднання (спроба {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
                try:
                    await client.disconnect()
                    await asyncio.sleep(2)
                except:
                    pass
        except Exception as e:
            print(f"❌ Помилка: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
    
    return None

def format_gift_message(gift):
    """Форматує повідомлення про подарунок"""
    emoji = gift.get('emoji', '🎁')
    message = f"🆕 **{emoji}**\n"
    message += f"┣ ID: `{gift['id']}`\n"
    
    # Ціна
    price_line = f"┣ Ціна: ⭐️ {gift['stars']} Stars"
    if gift.get('convert_stars'):
        price_line += f" → {gift['convert_stars']} ⭐️"
    message += price_line + "\n"
    
    # Статуси
    tags = []
    if gift.get('limited'):
        tags.append("🔥 Лімітований")
    if gift.get('birthday'):
        tags.append("🎂 ДН")
    if gift.get('require_premium'):
        tags.append("💎 Premium")
    if tags:
        message += f"┣ {', '.join(tags)}\n"
    
    # Доступність
    if gift.get('availability_remains') is not None and gift.get('availability_total'):
        remains = gift['availability_remains']
        total = gift['availability_total']
        
        if remains == 0:
            message += f"┣ ❌ РОЗПРОДАНО (0/{total:,})\n"
        else:
            percentage = (remains / total) * 100
            status_emoji = "🔴" if percentage <= 5 else "🟡" if percentage <= 20 else "🟢"
            message += f"┣ {status_emoji} {remains:,}/{total:,} ({percentage:.1f}%)\n"
            
            if percentage < 5:
                message += f"┣ ⚠️ **КРИТИЧНО!**\n"
    
    # Ліміт на юзера
    if gift.get('per_user_total'):
        message += f"┣ На юзера: {gift.get('per_user_remains', 0)}/{gift['per_user_total']}\n"
    
    # Статус покупки
    if gift.get('sold_out') or gift.get('availability_remains') == 0:
        message += f"┗ ❌ Неможливо купити\n"
    else:
        message += f"┗ ✅ Можна купити\n"
    
    return message

async def monitor_gifts(client):
    """Основна функція моніторингу"""
    print("=" * 60)
    print("🎁 БОТ МОНІТОРИНГУ ПОДАРУНКІВ ЗАПУЩЕНО!")
    print("=" * 60)
    print(f"📱 Інтервал: {CHECK_INTERVAL}с ({CHECK_INTERVAL//60}хв)")
    print(f"👤 User ID: {USER_ID}")
    print("=" * 60)
    
    known_gifts = load_known_gifts()
    first_run = len(known_gifts) == 0
    
    if first_run:
        print("ℹ️  Перший запуск - завантажую поточні подарунки...")
    
    while True:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_gifts = await get_available_gifts(client)
            
            if current_gifts is None:
                print(f"⚠️  [{current_time}] Не вдалося отримати подарунки")
                await asyncio.sleep(CHECK_INTERVAL)
                continue
            
            # Перевіряємо нові подарунки
            new_gifts = [g for gid, g in current_gifts.items() if gid not in known_gifts]
            
            if first_run:
                known_gifts = current_gifts
                save_known_gifts(known_gifts)
                print(f"✅ Завантажено {len(current_gifts)} подарунків")
                
                # Надсилаємо стартове повідомлення
                try:
                    await client.send_message(
                        USER_ID,
                        f"🤖 **БОТ ЗАПУЩЕНО!**\n\n"
                        f"📊 Відстежується: {len(current_gifts)} подарунків\n"
                        f"⏱ Інтервал: {CHECK_INTERVAL//60} хв\n"
                        f"📅 {current_time}"
                    )
                except Exception as e:
                    print(f"⚠️ Не вдалось надіслати стартове повідомлення: {e}")
                
                first_run = False
                
            elif new_gifts:
                print(f"\n🎉 [{current_time}] ЗНАЙДЕНО {len(new_gifts)} НОВИХ!")
                
                # Розбиваємо на частини
                chunk_size = 5
                total_chunks = (len(new_gifts) - 1) // chunk_size + 1
                
                for i in range(0, len(new_gifts), chunk_size):
                    chunk = new_gifts[i:i + chunk_size]
                    chunk_num = i // chunk_size + 1
                    
                    header = f"🎁 **НОВІ ПОДАРУНКИ!**"
                    if total_chunks > 1:
                        header += f" ({chunk_num}/{total_chunks})"
                    header += f"\n⏰ {current_time}\n\n"
                    
                    message = header + "".join(format_gift_message(g) + "\n" for g in chunk)
                    message += f"━━━━━━━━━━━━━━━━━━━━\n📊 Всього нових: {len(new_gifts)}"
                    
                    try:
                        await client.send_message(USER_ID, message)
                        print(f"✉️  Надіслано {chunk_num}/{total_chunks}")
                    except Exception as e:
                        print(f"❌ Помилка надсилання: {e}")
                    
                    if i + chunk_size < len(new_gifts):
                        await asyncio.sleep(2)
                
                known_gifts.update(current_gifts)
                save_known_gifts(known_gifts)
                print(f"✅ Оновлено базу\n")
                
            else:
                print(f"ℹ️  [{current_time}] Нових немає ({len(current_gifts)} всього)")
            
        except Exception as e:
            print(f"❌ Критична помилка: {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    """Головна функція"""
    print("\n🚀 Запуск бота...\n")
    
    # Створюємо клієнт
    client = TelegramClient('gift_monitor_session', API_ID, API_HASH)
    
    try:
        # Підключаємось (без бота, через user account)
        await client.start(phone=PHONE)
        print("✅ Авторизація успішна!")
        
        me = await client.get_me()
        print(f"👤 Користувач: {me.first_name} (ID: {me.id})\n")
        
        # Запускаємо моніторинг
        await monitor_gifts(client)
        
    except KeyboardInterrupt:
        print("\n⛔ Зупинка...")
        try:
            await client.send_message(USER_ID, "⛔ Бот зупинено")
        except:
            pass
        await client.disconnect()
        
    except Exception as e:
        print(f"\n❌ Фатальна помилка: {e}")
        import traceback
        traceback.print_exc()
        try:
            await client.send_message(USER_ID, f"❌ Бот впав: {e}")
        except:
            pass

if __name__ == '__main__':
    asyncio.run(main())
