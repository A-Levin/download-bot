FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY src/pyproject.toml src/uv.lock* ./

RUN uv sync --frozen --no-dev

COPY src .

CMD ["uv", "run", "python", "bot.py"]
