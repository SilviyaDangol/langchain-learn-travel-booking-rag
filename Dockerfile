FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
COPY . .
RUN uv sync
EXPOSE 8000
CMD ["uv", "run", "fastapi", "dev", "main.py", "--host", "0.0.0.0"]