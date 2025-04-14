FROM python:3.11-slim

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false \
  && poetry install --no-root

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
