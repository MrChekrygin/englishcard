import random
import psycopg2
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv('config.env')

print('Starting Telegram bot...')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Bot token
BOT_TOKEN = os.getenv('BOT_TOKEN')


# Database connection
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


# Bot initialization
state_storage = StateMemoryStorage()
bot = TeleBot(BOT_TOKEN, state_storage=state_storage)


# Commands
class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    PROGRESS = 'Прогресс'


# States
class MyStates(StatesGroup):
    adding_word = State()
    adding_translation = State()
    target_word = State()
    translate_word = State()
    another_words = State()


# Database operations
def register_user(telegram_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (telegram_id)
                VALUES (%s)
                ON CONFLICT (telegram_id) DO NOTHING
            """, (telegram_id,))


def get_user_words(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT w.target_word, w.translate_word, uw.correct_answers
                FROM words w
                JOIN user_words uw ON w.word_id = uw.word_id
                JOIN users u ON uw.user_id = u.user_id
                WHERE u.telegram_id = %s
            """, (user_id,))
            return cursor.fetchall()


def add_word_to_user(user_id, target_word, translate_word):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT word_id FROM words WHERE target_word = %s", (target_word,))
            word = cursor.fetchone()

            if word:
                word_id = word[0]
            else:
                cursor.execute("""
                    INSERT INTO words (target_word, translate_word) 
                    VALUES (%s, %s) RETURNING word_id
                """, (target_word, translate_word))
                word_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO user_words (user_id, word_id, correct_answers) 
                VALUES ((SELECT user_id FROM users WHERE telegram_id = %s), %s, 0)
                ON CONFLICT (user_id, word_id) DO NOTHING
            """, (user_id, word_id))


def delete_word_from_user(user_id, target_word):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM user_words 
                WHERE user_id = (SELECT user_id FROM users WHERE telegram_id = %s) 
                AND word_id = (
                    SELECT word_id FROM words WHERE target_word = %s
                )
            """, (user_id, target_word))


def update_correct_answer(user_id, target_word):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE user_words
                SET correct_answers = correct_answers + 1
                WHERE user_id = (SELECT user_id FROM users WHERE telegram_id = %s)
                AND word_id = (SELECT word_id FROM words WHERE target_word = %s)
            """, (user_id, target_word))


def get_progress(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(correct_answers), 0)
                FROM user_words
                WHERE user_id = (SELECT user_id FROM users WHERE telegram_id = %s)
            """, (user_id,))
            return cursor.fetchone()


# Bot handlers
def create_main_menu(user_words, target_word):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)

    options = [word for word in user_words if word[0] != target_word]
    options = random.sample(options, min(3, len(options)))
    options.append((target_word, ''))
    random.shuffle(options)

    word_buttons = [types.KeyboardButton(word[0]) for word in options]
    markup.add(*word_buttons)

    markup.row(
        types.KeyboardButton(Command.NEXT),
        types.KeyboardButton(Command.ADD_WORD),
        types.KeyboardButton(Command.DELETE_WORD),
        types.KeyboardButton(Command.PROGRESS)
    )

    return markup


@bot.message_handler(commands=['start', 'cards'])
def start_handler(message):
    user_id = message.chat.id
    register_user(user_id)
    user_words = get_user_words(user_id)

    if not user_words:
        bot.send_message(user_id, "У вас пока нет слов. Добавьте первое слово ➕.")
        return

    target_word, translate_word, _ = random.choice(user_words)
    markup = create_main_menu(user_words, target_word)

    bot.set_state(user_id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(user_id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate_word

    bot.send_message(user_id, f"Выберите правильный перевод:\n🇷🇺 {translate_word}", reply_markup=markup)


@bot.message_handler(func=lambda msg: msg.text == Command.PROGRESS)
def progress_handler(message):
    user_id = message.chat.id
    total_words, total_correct = get_progress(user_id)
    if total_words == 0:
        bot.send_message(user_id, "Вы еще не начали изучение слов.")
    else:
        bot.send_message(user_id, f"Вы изучаете {total_words} слов.\nПравильных ответов: {total_correct}.")


@bot.message_handler(func=lambda msg: msg.text == Command.NEXT)
def next_handler(message):
    start_handler(message)


@bot.message_handler(func=lambda msg: msg.text == Command.DELETE_WORD)
def delete_handler(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        delete_word_from_user(message.from_user.id, data.get('target_word'))
        bot.send_message(message.chat.id, f"Слово {data.get('target_word')} удалено.")

    bot.delete_state(message.from_user.id, message.chat.id)
    user_words = get_user_words(message.from_user.id)
    if not user_words:
        bot.send_message(message.chat.id, "У вас больше нет слов. Добавьте новые слова ➕.")
    else:
        start_handler(message)


@bot.message_handler(func=lambda msg: msg.text == Command.ADD_WORD)
def add_handler(message):
    bot.set_state(message.from_user.id, MyStates.adding_word, message.chat.id)
    bot.send_message(message.chat.id, "Отправьте новое слово на английском.")


@bot.message_handler(state=MyStates.adding_word, content_types=['text'])
def process_new_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['new_word'] = message.text

    bot.set_state(message.from_user.id, MyStates.adding_translation, message.chat.id)
    bot.send_message(message.chat.id, "Теперь отправьте перевод этого слова.")


@bot.message_handler(state=MyStates.adding_translation, content_types=['text'])
def process_translation(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        new_word = data.get('new_word')
        translation = message.text

        if new_word:
            add_word_to_user(message.from_user.id, new_word, translation)
            bot.send_message(message.chat.id, f"Слово '{new_word}' с переводом '{translation}' успешно добавлено.")
        else:
            bot.send_message(message.chat.id, "Произошла ошибка, попробуйте снова.")

    bot.delete_state(message.from_user.id, message.chat.id)
    start_handler(message)


@bot.message_handler(func=lambda msg: not msg.text.startswith('/'), content_types=['text'])
def general_message_handler(message):
    text = message.text.strip()

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data.get('target_word')
        translate_word = data.get('translate_word')

        if not target_word or not translate_word:
            bot.send_message(message.chat.id, "Что-то пошло не так. Попробуйте снова.")
            return

        if text.lower() == target_word.lower():
            response = f"Отлично!❤\n{target_word} -> {translate_word}"
            update_correct_answer(message.from_user.id, target_word)

        else:
            response = f"Неправильный ответ! Попробуйте снова. 🇷🇺 {translate_word}"

    user_words = get_user_words(message.from_user.id)
    markup = create_main_menu(user_words, target_word)
    bot.send_message(message.chat.id, response, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)
