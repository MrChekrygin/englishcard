# 📄 Документация Telegram-бота EnglishCard

## 📌 Описание

**EnglishCard** — это Telegram-бот для изучения английской лексики. Он позволяет пользователям добавлять новые слова, проверять свои знания, отслеживать прогресс и удалять ненужные слова.

---

## 🚀 Установка

1. **Клонируйте репозиторий:**

```bash
git clone https://github.com/MrChekrygin/englishcard
cd englishcard
```

2. **Создайте виртуальное окружение:**

```bash
python -m venv .venv
source .venv/bin/activate  # Для Linux/macOS
# или
.venv\Scripts\activate  # Для Windows
```

3. **Установите зависимости:**

```bash
pip install -r requirements.txt
```

4. **Создайте файл конфигурации `.env`:**

```env
DB_NAME=english_bot_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
BOT_TOKEN=your_bot_token
```

5. **Запустите бота:**

```bash
python telegram_bot.py
```

---

## 🗂️ Структура проекта

- `telegram_bot.py` — основной файл с логикой бота.
- `.env` — файл конфигурации с переменными окружения.
- `requirements.txt` — список зависимостей Python.

---

## ⚙️ Основной функционал

### 1️⃣ Старт и регистрация

- **Команда:** `/start`
- **Описание:** Регистрирует пользователя и отображает главное меню.

### 2️⃣ Добавление нового слова

- **Кнопка:** "Добавить слово ➕"
- **Процесс:**
  1. Введите английское слово.
  2. Введите его перевод.

### 3️⃣ Удаление слова

- **Кнопка:** "Удалить слово 🔙"
- **Описание:** Удаляет текущее слово из базы данных пользователя.

### 4️⃣ Проверка знаний

- **Кнопка:** "Далее ⏩"
- **Описание:** Показывает следующее слово для повторения.

### 5️⃣ Отслеживание прогресса

- **Кнопка:** "Прогресс"
- **Описание:** Отображает количество изучаемых слов и количество правильных ответов.

---

## 🗄️ Структура базы данных

### Таблица `users`

- `user_id` (PK) — идентификатор пользователя.
- `telegram_id` — ID пользователя в Telegram.

### Таблица `words`

- `word_id` (PK) — идентификатор слова.
- `target_word` — английское слово.
- `translate_word` — перевод слова.

### Таблица `user_words`

- `user_id` (FK) — идентификатор пользователя.
- `word_id` (FK) — идентификатор слова.
- `correct_answers` — количество правильных ответов.

### 📋 SQL-код для создания таблиц

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL
);

CREATE TABLE words (
    word_id SERIAL PRIMARY KEY,
    target_word VARCHAR(255) NOT NULL,
    translate_word VARCHAR(255) NOT NULL
);

CREATE TABLE user_words (
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    word_id INTEGER REFERENCES words(word_id) ON DELETE CASCADE,
    correct_answers INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, word_id)
);
```

---

## 🧩 Зависимости

- `pyTelegramBotAPI`
- `psycopg2-binary`
- `python-dotenv`

Установка зависимостей:

```bash
pip install -r requirements.txt
```

---

## ❗ Возможные ошибки

1. **Ошибка токена:**
   
   - Убедитесь, что `BOT_TOKEN` в файле `.env` указан без пробелов или комментариев на той же строке.

2. **Ошибка подключения к базе данных:**

   - Проверьте настройки базы данных в файле `.env`.
   - Убедитесь, что PostgreSQL запущен.

---

## 📞 Обратная связь

Если у вас есть вопросы или предложения, создайте issue в репозитории GitHub или свяжитесь с разработчиком.

