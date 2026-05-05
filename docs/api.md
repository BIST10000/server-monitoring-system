# API

Базовая авторизация: заголовок `X-Api-Key` должен содержать один из ключей из `API_KEYS`.

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
  - если `server_name` неизвестен — сервер будет создан автоматически (MVP)

### Metrics

- `POST /api/v1/metrics`
  - body: `{ "server_name": "srv-1", "name": "cpu_percent", "value": 12.3, "tags": { ... }, "ts": "2026-03-11T10:00:00Z" }`
- `GET /api/v1/metrics?server_id=<uuid>&name=cpu_percent&since=2026-03-11T00:00:00Z&limit=200`

### Alert rules / events (MVP)

- `POST /api/v1/alert-rules`
  - body: `{ "name": "CPU high", "metric_name": "cpu_percent", "comparator": ">", "threshold": 80, "window_seconds": 60, "enabled": true, "labels": { ... } }`
- `GET /api/v1/alert-rules`
- `POST /api/v1/alerts/evaluate` — запускает простую оценку правил и чистку старых метрик (MVP)
- `GET /api/v1/alerts?status=firing&limit=200`

## OpenAPI

Актуальный контракт смотрите в Swagger UI: `GET /docs` или JSON: `GET /openapi.json`.

