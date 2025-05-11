import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import aiohttp
from openai import AsyncOpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = os.getenv("API_URL", "http://localhost:5000")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def get_or_create_user(telegram_id, username):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/users/") as resp:
            users = await resp.json()
            user = next((u for u in users if u["telegram_id"] == telegram_id), None)
            if user:
                return user
        payload = {"telegram_id": telegram_id, "username": username}
        async with session.post(f"{API_URL}/users/", json=payload) as resp:
            return await resp.json()

async def create_reminder(user_id, chat_id, title, description, event_time, repeat_type, notification_time, tags=None):
    data = {
        "user_id": user_id,
        "chat_id": chat_id,
        "title": title,
        "description": description,
        "event_time": event_time,
        "repeat_type": repeat_type,
        "notification_time": notification_time,
        "tags": tags or []
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/reminders/", json=data) as resp:
            return await resp.json()

async def parse_reminder_with_gpt(text):
    now = datetime.now().isoformat(sep='T', timespec='seconds')
    prompt = (
        f"Сегодня: {now} (текущее время сервера). "
        "Ты помощник, который извлекает параметры напоминания из текста пользователя. "
        "Верни результат в JSON с ключами: "
        "title (строка), description (строка или null), event_time (строка в формате ISO 8601, например 2024-06-01T18:00:00), "
        "repeat_type (строка в формате cron или null, например '0 9 * * 1' для еженедельного напоминания в понедельник в 9:00, '0 8 * * *' для ежедневного в 8:00, null если без повтора), "
        "notification_time (строка в формате ISO 8601 или null), tags (список строк или пустой список). "
        "Примеры:\n"
        '{"title": "Позвонить маме", "description": "Позвонить маме по поводу дня рождения", "event_time": "2024-06-01T18:00:00", "repeat_type": null, "notification_time": "2024-06-01T17:50:00", "tags": ["личное"]}\n'
        '{"title": "Собрание", "description": null, "event_time": "2024-06-03T09:00:00", "repeat_type": "0 9 * * 1", "notification_time": null, "tags": ["работа", "встреча"]}\n'
        '{"title": "Пить воду", "description": "Напоминание пить воду каждое утро", "event_time": "2024-06-02T08:00:00", "repeat_type": "0 8 * * *", "notification_time": null, "tags": []}\n'
        f"Текст: {text}\n"
        "Ответ (только JSON):"
    )
    response = await openai_client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Ты парсер напоминаний. Всегда возвращай только валидный JSON. repeat_type всегда cron или null."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.1,
    )
    import json, re
    match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
    if match:
        return json.loads(match.group())
    else:
        raise ValueError("Не удалось распознать параметры напоминания.")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer("Привет! Просто напиши мне напоминание в свободной форме, например: 'Завтра в 19:00 позвонить маме'. Я всё пойму!")

@dp.message(Command("reminders"))
async def cmd_reminders(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/users/") as resp:
            users = await resp.json()
            user = next((u for u in users if u["telegram_id"] == message.from_user.id), None)
            if not user:
                await message.answer("Сначала напишите /start.")
                return
            async with session.get(f"{API_URL}/reminders/") as r2:
                reminders = await r2.json()
                user_reminders = [r for r in reminders if r["user_id"] == user["id"]]
                if not user_reminders:
                    await message.answer("У вас нет напоминаний.")
                    return
                # Формируем текст списка
                text = "\n\n".join(
                    f"{i+1}. {rem['title']} — {rem.get('event_time', '') or ''}"
                    for i, rem in enumerate(user_reminders)
                )
                # Формируем inline-кнопки для удаления
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=f"❌ Удалить: {rem['title']}",
                                callback_data=f"delete_reminder:{rem['id']}"
                            )
                        ]
                        for rem in user_reminders
                    ]
                )
                await message.answer(
                    text or "У вас нет напоминаний.",
                    reply_markup=keyboard
                )

@dp.callback_query(F.data.startswith("delete_reminder:"))
async def delete_reminder_callback(callback: CallbackQuery):
    reminder_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    # Получим id пользователя в базе
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/users/") as resp:
            users = await resp.json()
            user = next((u for u in users if u["telegram_id"] == user_id), None)
            if not user:
                await callback.answer("Ошибка пользователя. Напишите /start.", show_alert=True)
                return
            async with session.delete(f"{API_URL}/reminders/{reminder_id}?user_id={user['id']}") as resp2:
                if resp2.status == 204:
                    await callback.answer("Напоминание удалено!", show_alert=False)
                    # Обновим список
                    # Получаем оставшиеся напоминания
                    async with session.get(f"{API_URL}/reminders/") as r2:
                        reminders = await r2.json()
                        user_reminders = [r for r in reminders if r["user_id"] == user["id"]]
                        if not user_reminders:
                            await callback.message.edit_text("У вас нет напоминаний.", reply_markup=None)
                            return
                        text = "\n\n".join(
                            f"{i+1}. {rem['title']} — {rem.get('event_time', '') or ''}"
                            for i, rem in enumerate(user_reminders)
                        )
                        keyboard = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text=f"❌ Удалить: {rem['title']}",
                                        callback_data=f"delete_reminder:{rem['id']}"
                                    )
                                ]
                                for rem in user_reminders
                            ]
                        )
                        await callback.message.edit_text(text, reply_markup=keyboard)
                else:
                    data = await resp2.json()
                    msg = data.get("error", "Ошибка удаления.")
                    await callback.answer(msg, show_alert=True)

@dp.message()
async def handle_freeform(message: types.Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    try:
        params = await parse_reminder_with_gpt(message.text)
    except Exception as e:
        await message.answer("Не удалось распознать напоминание. Попробуйте переформулировать фразу, например: 'Завтра в 19:00 позвонить маме'.")
        return
    reminder = await create_reminder(
        user_id=user["id"],
        chat_id=message.chat.id,
        title=params.get("title", "Без названия"),
        description=params.get("description"),
        event_time=params.get("event_time"),
        repeat_type=params.get("repeat_type"),
        notification_time=params.get("notification_time"),
        tags=params.get("tags"),
    )
    await message.answer(f"Напоминание создано: {reminder['title']} на {reminder.get('event_time', '')}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))