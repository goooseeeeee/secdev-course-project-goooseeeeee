APP_NAME=app
PORT=8000

.PHONY: build up down logs health test

build:
	docker compose --profile dev build $(APP_NAME)

up:
	docker compose --profile dev up -d $(APP_NAME)

down:
	docker compose down

logs:
	docker compose logs -f $(APP_NAME)

health:
	docker compose ps

test:
	docker exec -it $$(docker compose ps -q $(APP_NAME)) id -u
