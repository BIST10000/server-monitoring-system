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

