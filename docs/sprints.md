# Спринты

Ниже — реалистичный план на 6 спринтов (по 1–2 недели). MVP уже реализует основу: API + БД + агент + Docker.

## Sprint 1 — MVP “телеметрия”

- **Backend**
  - CRUD серверов
  - Ingest heartbeat
  - Ingest метрик (по одной точке)
  - Авторизация по API ключу
  - Postgres + Alembic миграции
- **Agent**
  - Отправка heartbeat + cpu/mem/disk/loadavg
- **Ops**
  - `docker-compose.yml`, `healthcheck`, миграции при старте
- **Done criteria**
  - `docker compose up --build` поднимает API и БД
  - Swagger доступен и запросы работают

## Sprint 2 — Пакетный инжест + idempotency

- `POST /api/v1/metrics:batch` (батч из N метрик)
- Идемпотентность через `Idempotency-Key` + хранение “последних батчей”
- Ограничения по размеру батча, rate limits

## Sprint 3 — Алёртинг “по-взрослому”

- Фоновый планировщик/воркер (Celery/APS) для:
  - оценки правил по расписанию
  - ретеншн/чистка
- Дедупликация алёртов, состояние “firing/resolved”
- Webhook интеграция (Slack/Teams/Email) как выход алёртов

## Sprint 4 — Наблюдаемость сервиса

- Метрики API (Prometheus) + трассировка (OpenTelemetry)
- Структурированные логи + correlation id
- Дашборд (Grafana) для API/алёртов/инжеста

## Sprint 5 — Безопасность и доступы

- JWT/OAuth2, роли (RBAC), проект/тенант-модель
- Управление API ключами через UI/endpoint, ротация
- Аудит действий

## Sprint 6 — Масштабирование данных

- Партиционирование `metric_points` по времени (Postgres native partitioning)
- Архивация/агрегации (rollups)
- Экспорт в time-series storage (опционально): VictoriaMetrics/Prometheus remote write

