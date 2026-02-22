FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Pre-download NLTK corpora (words dictionary + Brown corpus for frequencies)
RUN uv run python -c "import nltk; nltk.download('words', quiet=True); nltk.download('brown', quiet=True)"

COPY productai/ productai/

ENV BASE_PATH=""

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "productai.app:app", "--host", "0.0.0.0", "--port", "8000"]
