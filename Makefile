COMPOSE=docker compose

up:
	$(COMPOSE) up --build -d

build:
	$(COMPOSE) build

start:
	$(COMPOSE) up -d

logs:
	$(COMPOSE) logs -f

down:
	$(COMPOSE) down -v

restart: down up


# ------------
# TESTES
# ------------

test-chipset:
	poetry run pytest -v microservice_chipset/tests

test-cov:
	poetry run pytest --cov=microservice_chipset microservice_chipset/tests
