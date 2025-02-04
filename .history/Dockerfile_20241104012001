FROM python:3.12-slim

# Установка poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.7.1

# Установка необходимых зависимостей и poetry
RUN apt-get update && apt-get install -y curl ca-certificates && \
    curl -sSL https://install.python-poetry.org | python - && \
    # Добавление poetry в PATH
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry && \
    apt-get remove -y curl && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Удаляем старую настройку PATH, так как теперь она не нужна
# ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Копирование файлов зависимостей
COPY src/pyproject.toml src/poetry.lock* ./

# Установка зависимостей
RUN poetry install --only main --no-interaction --no-ansi

# Копирование исходного кода
COPY src .

CMD ["poetry", "run", "python", "bot.py"] 