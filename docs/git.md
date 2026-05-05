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

