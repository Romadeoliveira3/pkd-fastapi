# Usando Python 3.11 como base
FROM python:3.11

# Definir diretório de trabalho
WORKDIR /app

# Copiar os arquivos do contexto raiz para dentro do contêiner
COPY ../pyproject.toml ../poetry.lock ./

# Instalar o Poetry
RUN pip install poetry

# Instalar as dependências do projeto
RUN poetry install --no-root --only main

# Copiar os arquivos do microserviço
COPY . .

# Definir comando de inicialização do serviço
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
