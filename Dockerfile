FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.9.6
ENV PATH="/root/.local/bin:${PATH}"

COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --only main

COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
