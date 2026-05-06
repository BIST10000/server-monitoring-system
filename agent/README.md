# Agent

Мини-агент, который отправляет heartbeat и базовые метрики в API.

## Запуск

```bash
cd agent
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt

set API_BASE_URL=http://localhost:8080
set API_KEY=dev-key-1
set SERVER_NAME=my-server-01
python agent.py
```

## Переменные окружения

- `API_BASE_URL` (default: `http://localhost:8080`) — базовый URL backend API
- `API_KEY` (default: `dev-key-1`) — значение для заголовка `X-Api-Key`
- `SERVER_NAME` (default: hostname) — имя сервера, под которым агент будет слать данные
- `AGENT_VERSION` (default: `0.1.0`) — версия агента, сохраняется в heartbeat
- `AGENT_INTERVAL_SECONDS` (default: `15`) — период отправки heartbeat+метрик
- `AGENT_TIMEOUT_SECONDS` (default: `10`) — timeout HTTP запросов (сек)
- `AGENT_DISK_PATH` (default: `/`) — путь, для которого считать `disk_used_percent`

## Какие метрики отправляет

Агент отправляет метрики по одной точке в `POST /api/v1/metrics` со временем `ts` в UTC:
- `cpu_percent`
- `mem_used_percent`
- `disk_used_percent` (tag: `path`)
- `loadavg_1m`, `loadavg_5m`, `loadavg_15m` (если поддерживается ОС)

