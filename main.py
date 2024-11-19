import asyncio
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.types import Message

# Инициализация базы данных
conn = sqlite3.connect('habits.db')
cursor = conn.cursor()

# Создаем таблицу для хранения пользователей и их привычек
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    meditation_count INTEGER DEFAULT 0,
    book_count INTEGER DEFAULT 0,
    fiz_count INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    last_meditation TEXT,
    last_book TEXT,
    last_fiz TEXT
)
''')
conn.commit()


# Функция для добавления нового пользователя
def add_user(user_id: int, username: str):
    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username) 
    VALUES (?, ?)
    ''', (user_id, username))
    conn.commit()


# Функция для обновления привычки
def update_habit(user_id: int, habit: str):
    today = datetime.now().strftime('%Y-%m-%d')
    column_count = f"{habit}_count"
    column_last = f"last_{habit}"

    # Проверка, обновляли ли сегодня
    cursor.execute(f'''
    SELECT {column_last} FROM users WHERE user_id = ?
    ''', (user_id,))
    last_date = cursor.fetchone()[0]

    if last_date != today:
        cursor.execute(f'''
        UPDATE users 
        SET {column_count} = {column_count} + 1, 
            total_points = total_points + 1,
            {column_last} = ?
        WHERE user_id = ?
        ''', (today, user_id))
        conn.commit()
        return True
    return False


# Функция для получения данных профиля
def get_profile(user_id: int):
    cursor.execute('''
    SELECT username, meditation_count, book_count, fiz_count, total_points
    FROM users WHERE user_id = ?
    ''', (user_id,))
    return cursor.fetchone()


# Функция для получения топа участников
def get_top_users():
    cursor.execute('''
    SELECT username, total_points FROM users 
    ORDER BY total_points DESC LIMIT 10
    ''')
    return cursor.fetchall()


dp = Dispatcher()


@dp.message(Command('start'))
async def start_command(message: types.Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username
    add_user(user_id, username)

    kb = [
        [types.InlineKeyboardButton(text='Информация о боте?', callback_data='about_bot')],
        [
            types.InlineKeyboardButton(text='Привычки', callback_data='habit'),
            types.InlineKeyboardButton(text='Топ участников', callback_data='top')
        ],
        [types.InlineKeyboardButton(text='Профиль', callback_data='profile')],
        [types.InlineKeyboardButton(text='Контакты', url='https://www.linkedin.com/in/rauan-seidaly-3b32b4328/')]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer('Добро пожаловать! Выбери, что нажать:', reply_markup=keyboard)


@dp.callback_query(F.data == "about_bot")
async def about_bot_callback(callback: types.CallbackQuery):
    await callback.message.answer('Данный бот создан для записи ежедневных привычек.')


@dp.callback_query(F.data == "habit")
async def habits_list(callback: types.CallbackQuery) -> None:
    kb_h = [
        [
            types.InlineKeyboardButton(text='Медитация', callback_data='meditation'),
            types.InlineKeyboardButton(text='Книга', callback_data='book'),
            types.InlineKeyboardButton(text='Физ. активность', callback_data='fiz')
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb_h)
    await callback.message.answer('Какую привычку ты уже выполнил?', reply_markup=keyboard)


@dp.callback_query(F.data.in_(['meditation', 'book', 'fiz']))
async def habit_callback(callback: types.CallbackQuery):
    habit = callback.data
    user_id = callback.from_user.id

    if update_habit(user_id, habit):
        await callback.message.answer(f'Отлично! Ты выполнил {habit} сегодня! ✅')
    else:
        await callback.message.answer(f'Ты уже выполнил {habit} сегодня. Попробуй завтра! ❌')


@dp.callback_query(F.data == 'profile')
async def show_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    profile = get_profile(user_id)

    if profile:
        username, meditation, book, fiz, points = profile
        await callback.message.answer(
            f'Твой профиль: {username}\n'
            f'Медитация: {meditation}\nКнига: {book}\nФиз. активность: {fiz}\n'
            f'Общие баллы: {points}'
        )
    else:
        await callback.message.answer('Профиль не найден.')


@dp.callback_query(F.data == 'top')
async def show_top(callback: types.CallbackQuery):
    top_users = get_top_users()
    if top_users:
        top_list = "\n".join(
            [f"{idx + 1}. {username} - {points} баллов" for idx, (username, points) in enumerate(top_users)])
        await callback.message.answer(f'🏆 Топ участников:\n{top_list}')
    else:
        await callback.message.answer('Топ участников пока пуст.')


@dp.message()
async def all_handler(message: Message) -> None:
    await message.answer('Пока что я этого не умею. Нажми то, что есть в меню, пожалуйста.')


async def main() -> None:
    token = "7841210563:AAEtf1DZLdl_Wr59OlCEKGzJrj_3weoRRP0"
    bot = Bot(token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
