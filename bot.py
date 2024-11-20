import requests
import telebot
from telebot import types
import os
import json

bot = telebot.TeleBot('7815819391:AAG3fqzpv8k1CFmm6Y06wYb2uo2D_ZoiyIY')

SETTINGS_FILE = "user_settings.json"

if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as file:
        user_settings = json.load(file)
else:
    user_settings = {}


def save_user_settings():
    with open(SETTINGS_FILE, "w") as file:
        json.dump(user_settings, file)


@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Найти книги по автору")
    btn2 = types.KeyboardButton("Найти книгу по названию")
    markup.row(btn1, btn2)
    bot.send_message(
        message.chat.id,
        f"Приветствую вас, {message.from_user.first_name}!",
        reply_markup=markup,
    )
    bot.send_message(
        message.chat.id,
        f"Для помощи с ботом введите /help.",
    )


@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(
        message.chat.id,
        f"Вы можете:\n"
        "1. Найти книги по названию. Для этого нажмите кнопку 'Найти книгу по названию'.\n"
        "2. Найти книги по автору. Для этого нажмите кнопку 'Найти книги по автору'.\n"
        "3. Настроить количество выводимых книг с помощью команды /settings.\n"
        "4. Попросить бота показать следующие книги, нажав кнопку 'Следующие книги'.\n"
    )


@bot.message_handler(commands=["settings"])
def settings(message):
    chat_id = str(message.chat.id)
    current_limit = user_settings.get(chat_id, {}).get("book_limit", 5)
    msg = bot.send_message(
        chat_id,
        f"Текущее количество выводимых книг: {current_limit}\n"
        "Введите новое значение от 1 до 10:"
    )
    bot.register_next_step_handler(msg, set_book_limit)


def set_book_limit(message):
    chat_id = str(message.chat.id)
    try:
        new_limit = int(message.text)
        if new_limit <= 0 or new_limit > 10:
            raise ValueError("Limit must be positive.")
        if chat_id not in user_settings:
            user_settings[chat_id] = {}
        user_settings[chat_id]["book_limit"] = new_limit
        save_user_settings()
        bot.send_message(chat_id, f"Количество выводимых книг успешно обновлено на {new_limit}.")
    except ValueError:
        bot.send_message(
            chat_id,
            "Пожалуйста, введите чило от 1 до 10. Попробуйте снова, введя команду /settings."
        )


@bot.message_handler(func=lambda message: message.text == "Найти книгу по названию")
def on_click_title(message):
    msg = bot.send_message(message.chat.id, "Введите название книги:")
    bot.register_next_step_handler(msg, process_title_input)


@bot.message_handler(func=lambda message: message.text == "Найти книги по автору")
def on_click_author(message):
    msg = bot.send_message(message.chat.id, "Введите автора книги:")
    bot.register_next_step_handler(msg, process_author_input)


def process_title_input(message):
    title = message.text
    send_books(message, title, search_type="title")


def process_author_input(message):
    author = message.text
    send_books(message, author, search_type="author")


def search_books(query, page=0, limit=5, search_type="title"):
    url = "https://openlibrary.org/search.json"
    params = {search_type: query, "page": page + 1}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        books = data.get("docs", [])
        if not books:
            return None

        results = {
            'books': [],
            'has_more': len(books) > limit
        }

        for book in books[:limit]:
            title = book.get("title", "Название не найдено")
            author = book.get("author_name", ["Автор не указан"])[0]
            year = book.get("first_publish_year", "Год не указан")
            cover_id = book.get("cover_i")
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "Обложка не найдена"
            book_key = book.get("key")
            read_url = f"https://openlibrary.org{book_key}" if book_key else "Ссылка для чтения недоступна"

            results['books'].append({
                "title": title,
                "author": author,
                "year": year,
                "cover_url": cover_url,
                "read_url": read_url
            })
        return results
    else:
        return None


def send_books(message, query, page=0, search_type="title"):
    chat_id = str(message.chat.id)
    limit = user_settings.get(chat_id, {}).get("book_limit", 5)
    results = search_books(query, page, limit, search_type)

    if results:
        for book in results['books']:
            bot.send_message(
                message.chat.id,
                f"Название: {book['title']}\n"
                f"Автор: {book['author']}\n"
                f"Год издания: {book['year']}\n"
                f"Читать: {book['read_url']}"
            )
            if book['cover_url'] != "Обложка не найдена":
                bot.send_photo(message.chat.id, book['cover_url'])

        if results['has_more']:
            markup = types.InlineKeyboardMarkup()
            next_btn = types.InlineKeyboardButton("Следующие книги", callback_data=f"next_{search_type}_{query}_{page + 1}")
            markup.add(next_btn)
            bot.send_message(message.chat.id, "Показать следующие книги:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Книги не найдены.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("next_"))
def callback_next(call):
    data = call.data.split("_")
    search_type = data[1]
    query = data[2]
    page = int(data[3])

    send_books(call.message, query, page, search_type)

@bot.message_handler(func=lambda message: True)
def unknown_command(message):
    bot.send_message(message.chat.id, "Извините, я не понял вашу команду. Введите /help, чтобы узнать доступные команды.")

bot.polling(none_stop=True)
