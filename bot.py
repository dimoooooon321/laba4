import requests
import telebot
from telebot import types

bot = telebot.TeleBot('7815819391:AAG3fqzpv8k1CFmm6Y06wYb2uo2D_ZoiyIY')


@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton("Найти книги по автору")
    btn2 = types.KeyboardButton("Найти книгу по названию")
    markup.row(btn1, btn2)
    bot.send_message(
        message.chat.id,
        f"Приветствую вас, {message.from_user.first_name}",
        reply_markup=markup,
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
    send_book_by_title(message, title)


def process_author_input(message):
    author = message.text
    bot.send_message(message.chat.id, "Открываю результаты поиска...")
    send_books_by_author(message, author)


# Функция для поиска книг по названию с пагинацией
def search_books_by_title(title, page=0):
    url = "https://openlibrary.org/search.json"
    params = {"title": title, "page": page + 1}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        books = data.get("docs", [])

        if not books:  # Если книг не найдено, возвращаем None
            return None

        results = {
            'books': [],
            'has_more': len(books) > 5
        }

        for book in books[:5]:
            title = book.get("title", "Название не найдено")
            author = book.get("author_name", ["Автор не указан"])[0]
            year = book.get("first_publish_year", "Год не указан")
            cover_id = book.get("cover_i")
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "Обложка не найдена"
            book_key = book.get("key")
            read_url = f"https://openlibrary.org{book_key}" if book_key else "Ссылка для чтения недоступна"
            download_url = f"https://openlibrary.org{book_key}/formats" if book_key else "Ссылка для скачивания недоступна"

            results['books'].append({
                "title": title,
                "author": author,
                "year": year,
                "cover_url": cover_url,
                "read_url": read_url,
                "download_url": download_url
            })
        return results
    else:
        return None


# Функция для поиска книг по автору с пагинацией
def search_books_by_author(author, page=0):
    url = "https://openlibrary.org/search.json"
    params = {"author": author, "page": page + 1}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        books = data.get("docs", [])

        if not books:  # Если книг не найдено, возвращаем None
            return None

        results = {
            'books': [],
            'has_more': len(books) > 5
        }

        for book in books[:5]:
            title = book.get("title", "Название не найдено")
            author = book.get("author_name", ["Автор не указан"])[0]
            year = book.get("first_publish_year", "Год не указан")
            cover_id = book.get("cover_i")
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "Обложка не найдена"
            book_key = book.get("key")
            read_url = f"https://openlibrary.org{book_key}" if book_key else "Ссылка для чтения недоступна"
            download_url = f"https://openlibrary.org{book_key}/formats" if book_key else "Ссылка для скачивания недоступна"

            results['books'].append({
                "title": title,
                "author": author,
                "year": year,
                "cover_url": cover_url,
                "read_url": read_url,
                "download_url": download_url
            })
        return results
    else:
        return None


# Функции для отправки книг с возможностью перелистывания
def send_book_by_title(message, title, page=0):
    results = search_books_by_title(title, page)

    if results:
        for book in results['books']:
            bot.send_message(
                message.chat.id,
                f"Название: {book['title']}\n"
                f"Автор: {book['author']}\n"
                f"Год издания: {book['year']}\n"
                f"Читать: {book['read_url']}\n"
                f"Скачать: {book['download_url']}"
            )
            if book['cover_url'] != "Обложка не найдена":
                bot.send_photo(message.chat.id, book['cover_url'])

        if results['has_more']:
            markup = types.InlineKeyboardMarkup()
            next_btn = types.InlineKeyboardButton("Следующие 5 книг", callback_data=f"next_title_{title}_{page + 1}")
            markup.add(next_btn)
            bot.send_message(message.chat.id, "Показать следующие 5 книг:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Книги не найдены.")



def send_books_by_author(message, author, page=0):
    results = search_books_by_author(author, page)

    if results:
        for book in results['books']:
            bot.send_message(
                message.chat.id,
                f"Название: {book['title']}\n"
                f"Автор: {book['author']}\n"
                f"Год издания: {book['year']}\n"
                f"Читать: {book['read_url']}\n"
                f"Скачать: {book['download_url']}"
            )
            if book['cover_url'] != "Обложка не найдена":
                bot.send_photo(message.chat.id, book['cover_url'])

        if results['has_more']:
            markup = types.InlineKeyboardMarkup()
            next_btn = types.InlineKeyboardButton("Следующие 5 книг", callback_data=f"next_author_{author}_{page + 1}")
            markup.add(next_btn)
            bot.send_message(message.chat.id, "Показать следующие 5 книг:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Книги не найдены.")


# Обработчик для кнопок "Следующие 5 книг"
@bot.callback_query_handler(func=lambda call: call.data.startswith("next_"))
def callback_next(call):
    data = call.data.split("_")
    search_type = data[1]
    query = data[2]
    page = int(data[3])

    if search_type == "title":
        send_book_by_title(call.message, query, page)
    elif search_type == "author":
        send_books_by_author(call.message, query, page)


bot.polling(none_stop=True)
