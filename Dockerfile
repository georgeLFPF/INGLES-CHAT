FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

# uv instala dependências bem mais rápido que o pip
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /bin/uv

WORKDIR /app

# Copiado antes do código: a camada de dependências só é refeita quando o requirements.txt muda.
# Sem RUN --mount: o manage.py constrói pelo Docker SDK, que não usa BuildKit.
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "front-end/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
