# Сервис мониторинга серверов

Каркас системы мониторинга: REST API для регистрации серверов и приёма телеметрии (heartbeat + метрики), простая модель алёртов (MVP), встроенная веб-панель, агент для отправки данных, Postgres для хранения, Docker Compose для локального запуска.

## Быстрый старт (Docker)

1) Поднимите стек:

```bash
docker compose up --build
```

2) Откройте сервисы:
- API Swagger UI: `http://localhost:8080/docs`
- OpenAPI JSON: `http://localhost:8080/openapi.json`
- Healthcheck: `http://localhost:8080/health`
- Веб-панель: `http://localhost:8080/ui`

## Конфигурация (env)

В `docker-compose.yml` backend читает переменные из `./.env.example` (см. `env_file`). Если хотите поменять значения:
- отредактируйте `.env.example` локально, или
- измените `env_file` в `docker-compose.yml` под ваш файл (например, `.env`) — это удобно для своей машины.

Ключевые переменные:
- **`API_KEYS`**: список допустимых ключей через запятую (например `dev-key-1,dev-key-2`)
- **`METRIC_RETENTION_DAYS`**: ретеншн метрик (чистка запускается при `POST /api/v1/alerts/evaluate` и из UI-кнопки)
- **`HEARTBEAT_STALE_SECONDS`**: через сколько секунд без heartbeat сервер считается “не ок” в UI
- **`UI_ENABLED`**: включает/выключает роуты UI (`/ui`)
- **`UI_REQUIRE_API_KEY`**: требовать ли API ключ для UI (по умолчанию UI открыт, а API защищено)

## Структура

- `backend/` — REST API (FastAPI), хранение данных (SQLAlchemy), миграции (Alembic), UI (`/ui`)
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

По умолчанию API требует заголовок `X-Api-Key` на всех `/api/v1/*` эндпоинтах. Допустимые ключи задаются через `API_KEYS`.

## Лицензия

MIT (см. `LICENSE`).

