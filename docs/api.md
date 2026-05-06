# API

## Авторизация

Все эндпоинты под префиксом `/api/v1` защищены API ключом.

- Заголовок: `X-Api-Key: <key>`
- Допустимые ключи: переменная окружения `API_KEYS` (через запятую)

Эндпоинты вне `/api/v1`:
- `GET /health` — без авторизации
- `GET /docs`, `GET /openapi.json` — без авторизации (Swagger/OpenAPI)
- `/ui/*` — зависит от `UI_REQUIRE_API_KEY` (см. `docs/architecture.md`)

## Endpoints (v1)

### Health

- `GET /health` → `{ "status": "ok" }`

### Servers

- `POST /api/v1/servers`
  - body: `{ "name": "srv-1", "environment": "prod", "labels": { ... } }`
- `GET /api/v1/servers?environment=prod`

### Heartbeats

- `POST /api/v1/heartbeats`
  - body: `{ "server_name": "srv-1", "agent_version": "0.1.0", "payload": { ... } }`
  - если `server_name` неизвестен — сервер будет создан автоматически (MVP, environment=`prod`, labels=`{}`)

### Metrics

- `POST /api/v1/metrics`
  - body: `{ "server_name": "srv-1", "name": "cpu_percent", "value": 12.3, "tags": { ... }, "ts": "2026-03-11T10:00:00Z" }`
- `GET /api/v1/metrics?server_id=<uuid>&name=cpu_percent&since=2026-03-11T00:00:00Z&limit=200`

### Alert rules / events (MVP)

- `POST /api/v1/alert-rules`
  - body: `{ "name": "CPU high", "metric_name": "cpu_percent", "comparator": ">", "threshold": 80, "window_seconds": 60, "enabled": true, "labels": { ... } }`
- `GET /api/v1/alert-rules`
- `DELETE /api/v1/alert-rules/{rule_id}`
- `POST /api/v1/alerts/evaluate` — запускает простую оценку правил и чистку старых метрик (MVP)
- `GET /api/v1/alerts?status=firing&limit=200`
- `POST /api/v1/alerts/{alert_id}/resolve`

## OpenAPI

Актуальный контракт смотрите в Swagger UI: `GET /docs` или JSON: `GET /openapi.json`.

