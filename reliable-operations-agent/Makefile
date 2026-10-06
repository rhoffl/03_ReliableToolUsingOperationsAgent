.PHONY: up down logs test reset
up:
	docker compose up --build
down:
	docker compose down
logs:
	docker compose logs -f
test:
	docker compose run --rm api pytest -q
reset:
	docker compose down -v
