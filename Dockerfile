# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

# uv instala dependências bem mais rápido que o pip
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /bin/uv

WORKDIR /app

# Cache persistente entre builds: só baixa de novo o que mudou no requirements.txt
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "front-end/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
