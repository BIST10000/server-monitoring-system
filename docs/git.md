# Git и процесс разработки

## Инициализация репозитория

```bash
git init
git add .
git commit -m "chore: bootstrap server monitoring system"
```

## Ветки

- `main` — стабильная ветка
- `feat/<short-name>` — фичи
- `fix/<short-name>` — багфиксы
- `chore/<short-name>` — инфраструктура/рефакторинг

## Коммиты (Conventional Commits)

- `feat:` новая функциональность
- `fix:` исправление багов
- `docs:` документация
- `chore:` инфраструктура/сборка/обновления
- `refactor:` рефакторинг без изменения поведения
- `test:` тесты

Пример:

```text
feat(api): add metrics batch ingest

Adds /api/v1/metrics:batch with idempotency key support.
```

## PR checklist

- Описание “что/почему”
- Тест-план (как проверить вручную)
- Нет секретов в коде (`.env` не коммитим)
- Миграции обновлены (если менялась схема)

## План работ (спринты)

Ниже — краткий роадмап разработки (перенесено из `sprints.md`).

### Sprint 1 — MVP “телеметрия”

- CRUD серверов
- Ingest heartbeat
- Ingest метрик (по одной точке)
- Авторизация по API ключу
- Postgres + Alembic миграции
- Агент: heartbeat + cpu/mem/disk/loadavg
- Ops: `docker-compose.yml`, `healthcheck`, миграции при старте
- Done: `docker compose up --build`, Swagger доступен и запросы работают

### Sprint 2 — Пакетный инжест + idempotency

- `POST /api/v1/metrics:batch` (батч из N метрик)
- Идемпотентность через `Idempotency-Key` + хранение “последних батчей”
- Ограничения по размеру батча, rate limits

### Sprint 3 — Алёртинг

- Планировщик/воркер (Celery/APS): оценка правил по расписанию, ретеншн/чистка
- Дедупликация алёртов, состояние “firing/resolved”
- Webhook интеграции (Slack/Teams/Email)

### Sprint 4 — Наблюдаемость сервиса

- Метрики API (Prometheus) + трассировка (OpenTelemetry)
- Структурированные логи + correlation id
- Дашборд (Grafana) для API/алёртов/инжеста

### Sprint 5 — Безопасность и доступы

- JWT/OAuth2, роли (RBAC), проект/тенант-модель
- Управление API ключами через UI/endpoint, ротация
- Аудит действий

### Sprint 6 — Масштабирование данных

- Партиционирование `metric_points` по времени (Postgres native partitioning)
- Архивация/агрегации (rollups)
- Экспорт в time-series storage (опционально): VictoriaMetrics/Prometheus remote write

