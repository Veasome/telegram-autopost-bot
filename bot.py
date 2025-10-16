import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta
import telebot
from telebot import types
from dotenv import load_dotenv

# Загрузка настроек
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID', '@severitynotfound')
ADMIN_ID = int(os.getenv('ADMIN_ID', '469085521'))

bot = telebot.TeleBot(BOT_TOKEN)

# База данных
def init_db():
    conn = sqlite3.connect('posts.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            time DATETIME NOT NULL,
            status TEXT DEFAULT 'scheduled'
        )
    ''')
    conn.commit()
    conn.close()

def save_post(text, post_time):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO posts (text, time) VALUES (?, ?)', (text, post_time))
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id

def get_posts(status=None):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    if status:
        cursor.execute('SELECT * FROM posts WHERE status = ? ORDER BY time', (status,))
    else:
        cursor.execute('SELECT * FROM posts ORDER BY time')
    posts = cursor.fetchall()
    conn.close()
    return posts

def delete_post(post_id):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

# Парсинг времени
def parse_time(time_str):
    time_str = time_str.strip().lower()
    now = datetime.now()
    
    if time_str.startswith('+'):
        if time_str.endswith('h'):
            hours = int(time_str[1:-1])
            return now + timedelta(hours=hours)
        elif time_str.endswith('d'):
            days = int(time_str[1:-1])
            return now + timedelta(days=days)
        else:
            minutes = int(time_str[1:])
            return now + timedelta(minutes=minutes)
    else:
        if ' ' in time_str:
            time_part, date_part = time_str.split(' ', 1)
            time_obj = datetime.strptime(time_part, '%H:%M').time()
            date_obj = datetime.strptime(date_part, '%d.%m.%Y').date()
            return datetime.combine(date_obj, time_obj)
        else:
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            scheduled = datetime.combine(now.date(), time_obj)
            if scheduled <= now:
                scheduled += timedelta(days=1)
            return scheduled

# Фоновая проверка постов
def start_scheduler():
    def check_posts():
        while True:
            conn = sqlite3.connect('posts.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, text FROM posts WHERE status = "scheduled" AND time <= ?', (datetime.now(),))
            
            for post_id, text in cursor.fetchall():
                try:
                    bot.send_message(CHANNEL_ID, text)
                    cursor.execute('UPDATE posts SET status = "sent" WHERE id = ?', (post_id,))
                    conn.commit()
                    bot.send_message(ADMIN_ID, f'✅ Пост #{post_id} опубликован!')
                except Exception as e:
                    print(f'Ошибка: {e}')
            
            conn.close()
            time.sleep(30)
    
    thread = threading.Thread(target=check_posts, daemon=True)
    thread.start()

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton('📅 Новый пост'),
        types.KeyboardButton('📋 Мои посты'),
        types.KeyboardButton('📊 Статистика'),
        types.KeyboardButton('❌ Удалить пост'),
        types.KeyboardButton('ℹ️ Помощь')
    ]
    markup.add(*buttons)
    return markup

# Обработчики команд
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, '❌ Доступ запрещен')
        return
    
    bot.send_message(
        message.chat.id,
        f'👋 Привет! Я бот для авто-постинга в {CHANNEL_ID}\n\n'
        'Выберите действие:',
        reply_markup=main_menu()
    )

user_data = {}

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text

    if text == '📅 Новый пост':
        user_data[message.chat.id] = {'step': 'waiting_time'}
        bot.send_message(
            message.chat.id,
            '🕒 *Когда опубликовать пост?*\n\n'
            '*Примеры:*\n'
            '+10 - через 10 минут\n'
            '18:00 - сегодня в 18:00\n'
            '14:30 25.12.2024 - конкретная дата\n\n'
            'Введите время:',
            parse_mode='Markdown',
            reply_markup=types.ReplyKeyboardRemove()
        )

    elif text == '📋 Мои посты':
        posts = get_posts('scheduled')
        if not posts:
            bot.send_message(message.chat.id, '📭 Нет запланированных постов')
            return
        
        response = '📋 *Ваши посты:*\n\n'
        for post in posts:
            time_str = datetime.strptime(post[2], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
            response += f'🆔 #{post[0]} - {time_str}\n📝 {post[1][:50]}...\n\n'
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown')

    elif text == '📊 Статистика':
        posts = get_posts()
        scheduled = len([p for p in posts if p[3] == 'scheduled'])
        sent = len([p for p in posts if p[3] == 'sent'])
        
        bot.send_message(
            message.chat.id,
            f'📊 *Статистика*\n\n'
            f'📝 Всего постов: {len(posts)}\n'
            f'⏳ Ожидают: {scheduled}\n'
            f'✅ Опубликовано: {sent}',
            parse_mode='Markdown'
        )

    elif text == '❌ Удалить пост':
        posts = get_posts('scheduled')
        if not posts:
            bot.send_message(message.chat.id, '❌ Нет постов для удаления')
            return
        
        markup = types.InlineKeyboardMarkup()
        for post in posts:
            time_str = datetime.strptime(post[2], '%Y-%m-%d %H:%M:%S').strftime('%d.%m %H:%M')
            markup.add(types.InlineKeyboardButton(
                f'❌ #{post[0]} - {time_str}',
                callback_data=f'delete_{post[0]}'
            ))
        
        bot.send_message(message.chat.id, '🗑 Выберите пост для удаления:', reply_markup=markup)

    elif text == 'ℹ️ Помощь':
        bot.send_message(
            message.chat.id,
            'ℹ️ *Помощь*\n\n'
            '*Форматы времени:*\n'
            '+10 - через 10 минут\n'
            '+1h - через 1 час\n'
            '+1d - через 1 день\n'
            '18:00 - сегодня в 18:00\n'
            '14:30 25.12.2024 - конкретная дата\n\n'
            'Бот проверяет посты каждые 30 секунд',
            parse_mode='Markdown'
        )

    else:
        # Обработка состояний
        chat_id = message.chat.id
        if chat_id in user_data:
            step = user_data[chat_id]['step']
            
            if step == 'waiting_time':
                try:
                    post_time = parse_time(text)
                    user_data[chat_id] = {'step': 'waiting_text', 'time': post_time}
                    bot.send_message(
                        chat_id,
                        f'🕒 Время: {post_time.strftime("%d.%m.%Y %H:%M")}\n\n'
                        '📝 Теперь введите текст поста:'
                    )
                except:
                    bot.send_message(chat_id, '❌ Неверный формат времени')

            elif step == 'waiting_text':
                post_time = user_data[chat_id]['time']
                post_id = save_post(text, post_time)
                del user_data[chat_id]
                
                bot.send_message(
                    chat_id,
                    f'✅ *Пост запланирован!*\n\n'
                    f'🆔 ID: #{post_id}\n'
                    f'🕒 Время: {post_time.strftime("%d.%m.%Y %H:%M")}\n'
                    f'📝 Текст: {text[:100]}...',
                    parse_mode='Markdown',
                    reply_markup=main_menu()
                )
        else:
            bot.send_message(chat_id, 'Выберите действие из меню:', reply_markup=main_menu())

# Обработка callback-запросов
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith('delete_'):
        post_id = call.data.split('_')[1]
        delete_post(post_id)
        bot.answer_callback_query(call.id, '✅ Пост удален')
        bot.edit_message_text('✅ Пост удален', call.message.chat.id, call.message.message_id)

# Запуск бота
if __name__ == "__main__":
    print("🚀 Запуск бота...")
    init_db()
    start_scheduler()
    print("✅ Бот запущен!")
    print("📱 Перейдите в Telegram и напишите /start вашему боту")
    bot.infinity_polling()