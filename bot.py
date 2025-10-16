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

print("🔥 НОВАЯ ВЕРСИЯ БОТА С МЕДИА И МЕНЮ!")


# Простой веб-сервер для UptimeRobot
def start_simple_server():
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class SimpleHandler(BaseHTTPRequestHandler):

            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write('🤖 Bot is alive and running!'.encode('utf-8'))

            def log_message(self, format, *args):
                pass

        server = HTTPServer(('0.0.0.0', 5000), SimpleHandler)
        print("🌐 Веб-сервер запущен на порту 5000")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Ошибка веб-сервера: {e}")


# База данных
def init_db():
    conn = sqlite3.connect('posts.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            media_type TEXT,
            media_file_id TEXT,
            time DATETIME NOT NULL,
            status TEXT DEFAULT 'scheduled'
        )
    ''')
    conn.commit()
    conn.close()


def save_post(text, post_time, media_type=None, media_file_id=None):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO posts (text, time, media_type, media_file_id) VALUES (?, ?, ?, ?)',
        (text, post_time, media_type, media_file_id))
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id


def get_posts(status=None):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    if status:
        cursor.execute('SELECT * FROM posts WHERE status = ? ORDER BY time',
                       (status, ))
    else:
        cursor.execute('SELECT * FROM posts ORDER BY time')
    posts = cursor.fetchall()
    conn.close()
    return posts


def delete_post(post_id):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id, ))
    conn.commit()
    conn.close()


# Парсинг времени
def parse_time(time_str):
    try:
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
    except:
        raise Exception("Неверный формат времени")


# Фоновая проверка постов
def start_scheduler():

    def check_posts():
        while True:
            conn = sqlite3.connect('posts.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, text, media_type, media_file_id FROM posts WHERE status = "scheduled" AND time <= ?',
                (datetime.now(), ))

            for post_id, text, media_type, media_file_id in cursor.fetchall():
                try:
                    if media_type == 'photo':
                        bot.send_photo(CHANNEL_ID, media_file_id, caption=text)
                    elif media_type == 'video':
                        bot.send_video(CHANNEL_ID, media_file_id, caption=text)
                    else:
                        bot.send_message(CHANNEL_ID, text)

                    cursor.execute(
                        'UPDATE posts SET status = "sent" WHERE id = ?',
                        (post_id, ))
                    conn.commit()
                    bot.send_message(ADMIN_ID,
                                     f'✅ Пост #{post_id} опубликован!')
                except Exception as e:
                    print(f'Ошибка публикации: {e}')

            conn.close()
            time.sleep(30)

    thread = threading.Thread(target=check_posts, daemon=True)
    thread.start()


# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('📅 Новый пост')
    btn2 = types.KeyboardButton('🖼️ Пост с медиа')
    btn3 = types.KeyboardButton('📋 Мои посты')
    btn4 = types.KeyboardButton('📊 Статистика')
    btn5 = types.KeyboardButton('❌ Удалить пост')
    btn6 = types.KeyboardButton('ℹ️ Помощь')

    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    return markup


# Хранилище данных пользователей
user_data = {}


# Обработчики команд
@bot.message_handler(commands=['start', 'menu'])
def start_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, '❌ Доступ запрещен')
        return

    print(f"🔄 Команда /start от {message.from_user.id}")

    bot.send_message(message.chat.id, f'👋 ПРИВЕТ! ЭТО НОВАЯ ВЕРСИЯ БОТА!\n\n'
                     f'Я бот для авто-постинга в {CHANNEL_ID}\n\n'
                     'Выберите действие:',
                     reply_markup=main_menu())


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.from_user.id != ADMIN_ID:
        return

    print(f"📨 Получено сообщение: {message.text}")

    text = message.text

    if text == '📅 Новый пост':
        user_data[message.chat.id] = {'step': 'waiting_time'}
        bot.send_message(
            message.chat.id, '🕒 *Когда опубликовать пост?*\n\n'
            '*Примеры:*\n• +10 - через 10 минут\n• +1h - через 1 час\n• 18:00 - сегодня в 18:00\n• 14:30 25.12.2024 - конкретная дата\n\nВведите время:',
            parse_mode='Markdown',
            reply_markup=types.ReplyKeyboardRemove())

    elif text == '🖼️ Пост с медиа':
        user_data[message.chat.id] = {'step': 'waiting_media'}
        bot.send_message(message.chat.id,
                         '📎 Пришлите фото или видео для поста',
                         reply_markup=types.ReplyKeyboardRemove())

    elif text == '📋 Мои посты':
        posts = get_posts('scheduled')
        if not posts:
            bot.send_message(message.chat.id,
                             '📭 Нет запланированных постов',
                             reply_markup=main_menu())
            return

        response = '📋 *Ваши посты:*\n\n'
        for post in posts:
            time_str = datetime.strptime(
                post[4], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
            media_icon = "📷" if post[
                2] == 'photo' else "🎥" if post[2] == 'video' else "📝"
            post_text = post[1][:50] + "..." if post[1] else "Медиа-пост"
            response += f'{media_icon} #{post[0]} - {time_str}\n{post_text}\n\n'

        bot.send_message(message.chat.id,
                         response,
                         parse_mode='Markdown',
                         reply_markup=main_menu())

    elif text == '📊 Статистика':
        posts = get_posts()
        scheduled = len([p for p in posts if p[5] == 'scheduled'])
        sent = len([p for p in posts if p[5] == 'sent'])

        bot.send_message(
            message.chat.id,
            f'📊 *Статистика*\n\n• Всего постов: {len(posts)}\n• Ожидают: {scheduled}\n• Опубликовано: {sent}',
            parse_mode='Markdown',
            reply_markup=main_menu())

    elif text == '❌ Удалить пост':
        posts = get_posts('scheduled')
        if not posts:
            bot.send_message(message.chat.id,
                             '❌ Нет постов для удаления',
                             reply_markup=main_menu())
            return

        markup = types.InlineKeyboardMarkup()
        for post in posts:
            time_str = datetime.strptime(
                post[4], '%Y-%m-%d %H:%M:%S').strftime('%d.%m %H:%M')
            markup.add(
                types.InlineKeyboardButton(f'❌ #{post[0]} - {time_str}',
                                           callback_data=f'delete_{post[0]}'))

        bot.send_message(message.chat.id,
                         '🗑 Выберите пост для удаления:',
                         reply_markup=markup)

    elif text == 'ℹ️ Помощь':
        bot.send_message(
            message.chat.id, 'ℹ️ *Помощь по боту*\n\n'
            '*Форматы времени:*\n• +10 - через 10 минут\n• +1h - через 1 час\n• 18:00 - сегодня в 18:00\n\n'
            '*Медиа-посты:*\nОтправляйте фото/видео после выбора соответствущей кнопки',
            parse_mode='Markdown',
            reply_markup=main_menu())

    else:
        chat_id = message.chat.id
        if chat_id in user_data:
            step = user_data[chat_id]['step']

            if step == 'waiting_time':
                try:
                    post_time = parse_time(text)
                    user_data[chat_id] = {
                        'step': 'waiting_text',
                        'time': post_time,
                        'media_type': user_data[chat_id].get('media_type'),
                        'media_file_id':
                        user_data[chat_id].get('media_file_id')
                    }
                    bot.send_message(
                        chat_id,
                        f'🕒 Время: {post_time.strftime("%d.%m.%Y %H:%M")}\n\n📝 Теперь введите текст поста:'
                    )
                except:
                    bot.send_message(chat_id, '❌ Неверный формат времени')

            elif step == 'waiting_text':
                post_time = user_data[chat_id]['time']
                media_type = user_data[chat_id].get('media_type')
                media_file_id = user_data[chat_id].get('media_file_id')

                post_id = save_post(text, post_time, media_type, media_file_id)
                del user_data[chat_id]

                media_info = " с медиа" if media_type else ""
                bot.send_message(
                    chat_id,
                    f'✅ Пост{media_info} запланирован!\n\n🆔 ID: #{post_id}\n🕒 Время: {post_time.strftime("%d.%m.%Y %H:%M")}',
                    reply_markup=main_menu())
        else:
            bot.send_message(chat_id,
                             'Выберите действие из меню:',
                             reply_markup=main_menu())


# Обработка медиа
@bot.message_handler(content_types=['photo', 'video'])
def handle_media(message):
    if message.from_user.id != ADMIN_ID:
        return

    chat_id = message.chat.id

    if chat_id in user_data and user_data[chat_id]['step'] == 'waiting_media':
        if message.photo:
            file_id = message.photo[-1].file_id
            user_data[chat_id] = {
                'step': 'waiting_time',
                'media_type': 'photo',
                'media_file_id': file_id
            }
            media_type = "📷 Фото"
        elif message.video:
            file_id = message.video.file_id
            user_data[chat_id] = {
                'step': 'waiting_time',
                'media_type': 'video',
                'media_file_id': file_id
            }
            media_type = "🎥 Видео"

        bot.send_message(
            chat_id,
            f'✅ {media_type} получено!\n\n🕒 Теперь введите время публикации:')
    else:
        bot.send_message(chat_id,
                         '❌ Сначала выберите "🖼️ Пост с медиа"',
                         reply_markup=main_menu())


# Обработка callback-запросов
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data.startswith('delete_'):
        post_id = call.data.split('_')[1]
        delete_post(post_id)
        bot.answer_callback_query(call.id, '✅ Пост удален')
        bot.edit_message_text('✅ Пост удален', call.message.chat.id,
                              call.message.message_id)


# Запуск бота
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 ЗАПУСК НОВОЙ ВЕРСИИ БОТА!")
    print("=" * 50)

    # Запуск веб-сервера
    try:
        web_thread = threading.Thread(target=start_simple_server, daemon=True)
        web_thread.start()
        time.sleep(1)
        print("🌐 Веб-сервер запущен на порту 5000")
    except Exception as e:
        print(f"❌ Ошибка веб-сервера: {e}")

    init_db()
    start_scheduler()

    print("✅ Бот инициализирован!")
    print("📱 Ожидание сообщений...")

    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
