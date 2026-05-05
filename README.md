# Сервис мониторинга серверов

Production-ready каркас системы мониторинга: API для регистрации серверов, приёма heartbeat/метрик, простая модель алёртов, агент для отправки данных, Postgres для хранения, Docker Compose для локального запуска, документация и план работ по спринтам.

## Быстрый старт (Docker)

1) (Опционально) Скопируйте переменные окружения, если хотите менять значения:

```bash
copy .env.example .env
```

2) Запустите стек:

```bash
docker compose up --build
```

3) API:
- Swagger UI: `http://localhost:8080/docs`
- OpenAPI JSON: `http://localhost:8080/openapi.json`
- Healthcheck: `http://localhost:8080/health`

## Структура

- `backend/` — REST API (FastAPI), хранение данных (SQLAlchemy), миграции (Alembic)
- `agent/` — лёгкий агент (Python) для отправки heartbeat/метрик на API
- `docs/` — архитектура, API-контракты, спринты, гайд по Git/процессу

## Документация

- `docs/architecture.md`
- `docs/api.md`
- `docs/sprints.md`
- `docs/git.md`

## Локальная разработка (без Docker)

Backend:

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

## Лицензия

MIT (см. `LICENSE`).

