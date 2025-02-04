# YouTube Downloader Telegram Bot

Telegram бот для скачивания видео с YouTube с учетом ограничений Telegram API по размеру файла (50MB).

## Возможности

- Показывает список доступных форматов видео
- Отображает размер файла и детали формата
- Скачивает видео размером до 50MB
- Показывает прогресс загрузки
- Обрабатывает ошибки

## Установка

### Использование Poetry (для разработки)

1. Установите Poetry:
    curl -sSL https://install.python-poetry.org | python3 -

2. Установите зависимости:
    cd src
    poetry install

3. Активируйте виртуальное окружение:
    poetry shell

4. Запустите бота:
    poetry run python bot.py

### Использование Docker

1. Создайте файл `.env` в директории `src`:
    API_TOKEN=your_telegram_bot_token

2. Запустите с помощью Docker Compose:
    docker-compose up -d

## Использование

1. Запустите бота командой `/start`
2. Отправьте ссылку на YouTube видео
3. Выберите формат, отправив его ID
4. Дождитесь завершения загрузки

## Ограничения

- Максимальный размер файла: 50MB (ограничение Telegram API)
- Поддерживаются только ссылки на YouTube

## Структура проекта

project-root/
│
├── docker-compose.yml
├── Dockerfile
├── README.md
└── src/
    ├── bot.py
    ├── pyproject.toml
    ├── poetry.lock
    └── .env

## Разработка

### Команды Poetry

- Добавление новых зависимостей:
    poetry add package_name

- Обновление зависимостей:
    poetry update

- Форматирование кода:
    poetry run black .
    poetry run isort .

- Проверка кода:
    poetry run flake8
