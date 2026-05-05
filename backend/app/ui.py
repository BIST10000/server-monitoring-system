from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crud
from app.db import get_db
from app.models import Heartbeat, Server
from app.security import require_api_key
from app.settings import settings


def _layout(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #0b1020;
      --card: #111a33;
      --text: #e8ecff;
      --muted: #aab3d6;
      --accent: #6ea8fe;
      --bad: #ff6b6b;
      --ok: #51cf66;
      --border: rgba(255,255,255,.08);
    }}
    body {{
      margin: 0;
      background: radial-gradient(1200px 800px at 15% 10%, #19224a 0%, var(--bg) 45%, #060a14 100%);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Liberation Sans", sans-serif;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    header {{
      position: sticky; top: 0; backdrop-filter: blur(10px);
      background: rgba(11,16,32,.65); border-bottom: 1px solid var(--border);
    }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 18px 16px; }}
    .top {{ display: flex; align-items: center; gap: 12px; justify-content: space-between; flex-wrap: wrap; }}
    .brand {{ display:flex; gap: 10px; align-items: baseline; }}
    .brand b {{ letter-spacing: .2px; }}
    .nav {{ display:flex; gap: 10px; flex-wrap: wrap; }}
    .pill {{
      display:inline-block; padding: 8px 10px; border-radius: 999px;
      border: 1px solid var(--border); background: rgba(255,255,255,.03);
    }}
    .grid {{ display:grid; grid-template-columns: 1fr; gap: 12px; }}
    @media (min-width: 900px) {{ .grid.cols-2 {{ grid-template-columns: 1fr 1fr; }} }}
    .card {{
      border: 1px solid var(--border); background: rgba(17,26,51,.75);
      border-radius: 16px; padding: 14px 14px;
      box-shadow: 0 10px 30px rgba(0,0,0,.25);
    }}
    h1 {{ font-size: 18px; margin: 0; }}
    h2 {{ font-size: 15px; margin: 0 0 10px 0; color: var(--muted); font-weight: 600; }}
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
    .muted {{ color: var(--muted); }}
    .badge {{
      display:inline-block; padding: 2px 8px; border-radius: 999px;
      border: 1px solid var(--border); font-size: 12px;
    }}
    .badge.ok {{ color: var(--ok); border-color: rgba(81,207,102,.35); background: rgba(81,207,102,.08); }}
    .badge.bad {{ color: var(--bad); border-color: rgba(255,107,107,.35); background: rgba(255,107,107,.08); }}
    input, select, textarea {{
      width: 100%; box-sizing: border-box;
      padding: 10px 10px; border-radius: 12px;
      border: 1px solid var(--border); background: rgba(0,0,0,.18);
      color: var(--text);
      outline: none;
    }}
    textarea {{ min-height: 110px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }}
    .row {{ display:grid; grid-template-columns: 1fr; gap: 10px; }}
    @media (min-width: 700px) {{ .row.cols-2 {{ grid-template-columns: 1fr 1fr; }} }}
    .btn {{
      display:inline-block; padding: 10px 12px; border-radius: 12px;
      border: 1px solid rgba(110,168,254,.35);
      background: rgba(110,168,254,.12);
      color: var(--text); cursor: pointer;
    }}
    .btn:hover {{ filter: brightness(1.07); }}
    pre {{
      margin: 0; padding: 12px; border-radius: 14px;
      border: 1px solid var(--border);
      background: rgba(0,0,0,.22);
      overflow: auto;
    }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }}
    .hint {{ font-size: 12px; color: var(--muted); }}
  </style>
</head>
<body>
  <header>
    <div class="wrap top">
      <div class="brand">
        <b>Сервис мониторинга серверов</b>
        <span class="muted">v 0.2</span>
      </div>
      <nav class="nav">
        <a class="pill" href="/ui">Главная</a>
        <a class="pill" href="/ui/servers/new">Добавить сервер</a>
        <a class="pill" href="/ui/alert-rules">Алёрт-правила</a>
        <a class="pill" href="/ui/alerts">Алёрты</a>
        <a class="pill" href="/ui/agent-config">Конфиг агента</a>
      </nav>
    </div>
  </header>
  <main class="wrap">
    {body}
  </main>
</body>
</html>"""


def _fmt_dt(dt: Any) -> str:
    if not dt:
        return "—"
    if isinstance(dt, datetime):
        try:
            return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except Exception:
            return dt.isoformat()
    return str(dt)


def _alert_status_label(status: str) -> tuple[str, str]:
    if status == "resolved":
        return ("ok", "решено")
    if status == "firing":
        return ("bad", "активный")
    return ("bad", status)


deps = []
if settings.ui_require_api_key:
    deps = [Depends(require_api_key)]

router = APIRouter(prefix="/ui", tags=["ui"], dependencies=deps)


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> str:
    servers = crud.list_servers(db)

    latest_hb = dict(
        db.execute(select(Heartbeat.server_id, func.max(Heartbeat.created_at)).group_by(Heartbeat.server_id)).all()
    )
    now = datetime.now(timezone.utc)

    rows = []
    for s in servers:
        last = latest_hb.get(s.id)
        stale = False
        if last is None:
            stale = True
        else:
            try:
                stale = (now - last).total_seconds() > settings.heartbeat_stale_seconds
            except Exception:
                stale = True

        status_badge = '<span class="badge bad">не ок</span>' if stale else '<span class="badge ok">ok</span>'
        rows.append(
            "<tr>"
            f"<td><a href='/ui/servers/{s.id}'><code>{html.escape(s.name)}</code></a></td>"
            f"<td>{html.escape(s.environment)}</td>"
            f"<td>{status_badge}</td>"
            f"<td class='muted'>{html.escape(_fmt_dt(last))}</td>"
            f"<td class='muted'>{html.escape(_fmt_dt(s.created_at))}</td>"
            "</tr>"
        )

    body = f"""
    <div class="grid cols-2">
      <section class="card">
        <h2>Сервера</h2>
        <table>
          <thead>
            <tr><th>Сервер</th><th>Окружение</th><th>Статус</th><th>Последний heartbeat</th><th>Создан</th></tr>
          </thead>
          <tbody>
            {''.join(rows) if rows else '<tr><td colspan="5" class="muted">Пока нет серверов. Агент создаст их автоматически при первом heartbeat.</td></tr>'}
          </tbody>
        </table>
        <div class="hint" style="margin-top:10px">
          Нет heartbeat = сервер не отвечает <code>{settings.heartbeat_stale_seconds}</code> секунд.
        </div>
      </section>
      <section class="card">
        <h2>Быстрые действия</h2>
        <div class="row">
          <a class="btn" href="/docs">API документация</a>
          <a class="btn" href="/ui/agent-config">Сгенерировать конфиг агента</a>
        </div>
      </section>
    </div>
    """
    return _layout("Главная", body)


@router.get("/servers/new", response_class=HTMLResponse)
def new_server_form() -> str:
    body = """
    <section class="card">
      <h2>Добавить сервер</h2>
      <form method="post" action="/ui/servers/new">
        <div class="row cols-2">
          <label>Имя сервера<br/><input name="name" placeholder="srv-01" required /></label>
          <label>Окружение<br/><input name="environment" placeholder="prod" value="prod" /></label>
        </div>
        <label style="display:block;margin-top:10px">Метки (JSON, опционально)<br/>
          <textarea name="labels" placeholder='{"role":"db","zone":"ru-1"}'></textarea>
        </label>
        <div style="margin-top:10px">
          <button class="btn" type="submit">Создать</button>
          <a class="pill" href="/ui">Назад</a>
        </div>
      </form>
    </section>
    """
    return _layout("Новый сервер", body)


@router.post("/servers/new")
def create_server_from_form(
    name: str = Form(...),
    environment: str = Form("prod"),
    labels: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    import json

    labels_obj: dict = {}
    if labels.strip():
        try:
            labels_obj = json.loads(labels)
            if not isinstance(labels_obj, dict):
                raise ValueError("labels must be an object")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid labels JSON: {e}")

    try:
        crud.create_server(db, name=name.strip(), environment=environment.strip() or "prod", labels=labels_obj)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RedirectResponse(url="/ui", status_code=303)


@router.get("/servers/{server_id}", response_class=HTMLResponse)
def server_details(server_id: str, db: Session = Depends(get_db)) -> str:
    from uuid import UUID

    try:
        sid = UUID(server_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid server id")

    s = db.scalar(select(Server).where(Server.id == sid))
    if s is None:
        raise HTTPException(status_code=404, detail="Server not found")

    metrics = crud.list_metric_points(db, server_id=str(s.id), limit=60)
    alerts = crud.list_alert_events(db, server_id=str(s.id), limit=20)
    rules_by_id = {str(r.id): r.name for r in crud.list_alert_rules(db)}

    m_rows = "".join(
        f"<tr><td><code>{html.escape(m.name)}</code></td><td>{m.value:.2f}</td><td class='muted'>{html.escape(_fmt_dt(m.ts))}</td></tr>"
        for m in metrics
    )
    a_rows = "".join(
        (lambda badge_class, badge_text: (
        "<tr>"
        f"<td><span class='badge {badge_class}'>{html.escape(badge_text)}</span></td>"
        f"<td><code>{html.escape(rules_by_id.get(str(a.rule_id), str(a.rule_id)))}</code></td>"
        f"<td>{html.escape(a.message)}</td>"
        f"<td class='muted'>{html.escape(_fmt_dt(a.created_at))}</td>"
        "</tr>"
        ))(*_alert_status_label(a.status))
        for a in alerts
    )

    body = f"""
    <div class="grid cols-2">
      <section class="card">
        <h2>Сервер</h2>
        <div><b>{html.escape(s.name)}</b> <span class="badge">{html.escape(s.environment)}</span></div>
        <div class="muted" style="margin-top:6px">id: <code>{html.escape(str(s.id))}</code></div>
        <div class="muted">created: <code>{html.escape(_fmt_dt(s.created_at))}</code></div>
        <div style="margin-top:10px"><a class="pill" href="/ui">← на главную</a></div>
      </section>
      <section class="card">
        <h2>Подсказка</h2>
        <div class="muted">
          Здесь показаны последние метрики, которые агент отправляет в <code>/api/v1/metrics</code>.
          Heartbeat отправляется отдельно в <code>/api/v1/heartbeats</code>.
        </div>
      </section>
      <section class="card">
        <h2>Последние метрики</h2>
        <table>
          <thead><tr><th>Метрика</th><th>Значение</th><th>Время</th></tr></thead>
          <tbody>{m_rows if m_rows else '<tr><td colspan="3" class="muted">Пока нет метрик</td></tr>'}</tbody>
        </table>
      </section>
      <section class="card">
        <h2>Последние алёрты по серверу</h2>
        <table>
          <thead><tr><th>Статус</th><th>Правило</th><th>Сообщение</th><th>Создан</th></tr></thead>
          <tbody>{a_rows if a_rows else '<tr><td colspan="4" class="muted">Пока нет алёртов</td></tr>'}</tbody>
        </table>
      </section>
    </div>
    """
    return _layout(f"Сервер {s.name}", body)


@router.get("/alert-rules/new", response_class=HTMLResponse)
def new_alert_rule_form(error: str | None = None) -> str:
    banner = ""
    if error:
        banner = f"<div class='hint' style='margin-bottom:10px;color:var(--bad)'>Ошибка: {html.escape(error)}</div>"
    body = f"""
    <section class="card">
      <h2>Создать алёрт-правило</h2>
      {banner}
      <form method="post" action="/ui/alert-rules/new">
        <label>Название<br/><input name="name" placeholder="CPU high" required /></label>
        <div class="row cols-2" style="margin-top:10px">
          <label>Имя метрики<br/><input name="metric_name" placeholder="cpu_percent" required /></label>
          <label>Оператор сравнения<br/>
            <select name="comparator">
              <option value=">">&gt;</option>
              <option value=">=">&gt;=</option>
              <option value="<">&lt;</option>
              <option value="<=">&lt;=</option>
            </select>
          </label>
        </div>
        <div class="row cols-2" style="margin-top:10px">
          <label>Порог<br/><input name="threshold" type="number" step="0.01" value="80" required /></label>
          <label>Окно (секунды)<br/><input name="window_seconds" type="number" value="60" required /></label>
        </div>
        <div class="row cols-2" style="margin-top:10px">
          <label>Включено<br/>
            <select name="enabled">
              <option value="true" selected>true</option>
              <option value="false">false</option>
            </select>
          </label>
          <label>Метки (JSON, опционально)<br/>
            <input name="labels" placeholder='{{"severity":"warning"}}' />
          </label>
        </div>
        <div style="margin-top:10px">
          <button class="btn" type="submit">Создать</button>
          <a class="pill" href="/ui/alert-rules">К списку правил</a>
        </div>
      </form>
    </section>
    """
    return _layout("Новое алёрт-правило", body)


@router.get("/alert-rules", response_class=HTMLResponse)
def alert_rules_page(deleted: str | None = None, db: Session = Depends(get_db)) -> str:
    rules = crud.list_alert_rules(db)
    rows = "".join(
        "<tr>"
        f"<td><code>{html.escape(r.name)}</code></td>"
        f"<td><code>{html.escape(r.metric_name)}</code></td>"
        f"<td><code>{html.escape(r.comparator)} {r.threshold:g}</code></td>"
        f"<td>{r.window_seconds}s</td>"
        f"<td><span class='badge {'ok' if r.enabled else 'bad'}'>{'включено' if r.enabled else 'выключено'}</span></td>"
        f"<td class='muted'>{html.escape(_fmt_dt(r.created_at))}</td>"
        "<td>"
        f"<form method='post' action='/ui/alert-rules/{r.id}/delete' onsubmit=\"return confirm('Удалить правило?');\" style='display:inline'>"
        "<button class='btn' type='submit'>Удалить</button>"
        "</form>"
        "</td>"
        "</tr>"
        for r in rules
    )
    banner = ""
    if deleted == "1":
        banner = "<div class='hint' style='margin-bottom:10px'>Правило удалено.</div>"
    body = f"""
    <section class="card">
      <h2>Алёрт-правила</h2>
      {banner}
      <div style="margin-bottom:10px">
        <a class="btn" href="/ui/alert-rules/new">Создать правило</a>
      </div>
      <table>
        <thead><tr><th>Название</th><th>Метрика</th><th>Условие</th><th>Окно</th><th>Статус</th><th>Создано</th><th>Действие</th></tr></thead>
        <tbody>{rows if rows else '<tr><td colspan="7" class="muted">Пока нет алёрт-правил</td></tr>'}</tbody>
      </table>
    </section>
    """
    return _layout("Алёрт-правила", body)


@router.post("/alert-rules/new")
def create_alert_rule_from_form(
    name: str = Form(...),
    metric_name: str = Form(...),
    comparator: str = Form(">"),
    threshold: float = Form(...),
    window_seconds: int = Form(60),
    enabled: str = Form("true"),
    labels: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    import json

    labels_obj: dict = {}
    if labels.strip():
        try:
            labels_obj = json.loads(labels)
            if not isinstance(labels_obj, dict):
                raise ValueError("labels must be an object")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid labels JSON: {e}")

    try:
        crud.create_alert_rule(
            db,
            name=name.strip(),
            metric_name=metric_name.strip(),
            comparator=comparator.strip(),
            threshold=float(threshold),
            window_seconds=int(window_seconds),
            enabled=(enabled.lower() == "true"),
            labels=labels_obj,
        )
    except IntegrityError:
        return RedirectResponse(url="/ui/alert-rules/new?error=Rule+with+this+name+already+exists", status_code=303)
    except Exception:
        return RedirectResponse(url="/ui/alert-rules/new?error=Failed+to+create+rule", status_code=303)
    return RedirectResponse(url="/ui/alert-rules", status_code=303)


@router.post("/alert-rules/{rule_id}/delete")
def delete_alert_rule_from_ui(rule_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    from uuid import UUID

    try:
        UUID(rule_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid alert rule id")

    deleted = crud.delete_alert_rule(db, rule_id=rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return RedirectResponse(url="/ui/alert-rules?deleted=1", status_code=303)


@router.get("/alerts", response_class=HTMLResponse)
def alerts(evaluated: str | None = None, status: str | None = None, db: Session = Depends(get_db)) -> str:
    items = crud.list_alert_events(db, status=status, limit=200)
    rules_by_id = {str(r.id): r.name for r in crud.list_alert_rules(db)}
    rows = "".join(
        (lambda badge_class, badge_text: (
        "<tr>"
        f"<td><span class='badge {badge_class}'>{html.escape(badge_text)}</span></td>"
        f"<td class='muted'><code>{html.escape(str(a.server_id))}</code></td>"
        f"<td><code>{html.escape(rules_by_id.get(str(a.rule_id), str(a.rule_id)))}</code></td>"
        f"<td>{html.escape(a.message)}</td>"
        f"<td class='muted'>{html.escape(_fmt_dt(a.created_at))}</td>"
        f"<td>{'' if a.status == 'resolved' else f'''<form method="post" action="/ui/alerts/{a.id}/resolve" style="display:inline"><button class="btn" type="submit">Решено</button></form>'''}</td>"
        "</tr>"
        ))(*_alert_status_label(a.status))
        for a in items
    )
    banner = ""
    if evaluated == "1":
        banner = "<div class='hint' style='margin-top:10px'>Проверка правил выполнена.</div>"
    body = f"""
    <section class="card">
      <h2>Алёрты</h2>
      <div class="hint">Фильтр: <a class="pill" href="/ui/alerts">все</a> <a class="pill" href="/ui/alerts?status=firing">активные</a> <a class="pill" href="/ui/alerts?status=resolved">решённые</a></div>
      <div style="margin-top:10px">
        <form method="post" action="/ui/alerts/evaluate" style="display:inline">
          <button class="btn" type="submit">Запустить проверку правил (MVP)</button>
        </form>
      </div>
      {banner}
      <table style="margin-top:10px">
        <thead><tr><th>Статус</th><th>Сервер</th><th>Правило</th><th>Сообщение</th><th>Создан</th><th>Действие</th></tr></thead>
        <tbody>{rows if rows else '<tr><td colspan="6" class="muted">Пока нет алёртов</td></tr>'}</tbody>
      </table>
    </section>
    """
    return _layout("Alerts", body)


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert_from_ui(alert_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    from uuid import UUID

    try:
        UUID(alert_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid alert id")

    updated = crud.set_alert_event_status(db, alert_id=alert_id, status="resolved")
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")

    return RedirectResponse(url="/ui/alerts", status_code=303)


@router.post("/alerts/evaluate")
def evaluate_alerts_from_ui(db: Session = Depends(get_db)) -> RedirectResponse:
    crud.evaluate_alert_rules(db)
    crud.purge_old_metrics(db)
    return RedirectResponse(url="/ui/alerts?evaluated=1", status_code=303)


@router.get("/agent-config", response_class=HTMLResponse)
def agent_config_form(
    api_base_url: str = "http://localhost:8080",
    api_key: str = "dev-key-1",
    server_name: str = "",
    disk_path: str = "/",
) -> str:
    server_name_line = ""
    if server_name.strip():
        server_name_line = f"set SERVER_NAME={html.escape(server_name)}\n"

    body = f"""
    <section class="card">
      <h2>Конфиг агента (GUI → готовый конфиг)</h2>
      <form method="get" action="/ui/agent-config">
        <div class="row cols-2">
          <label>Базовый URL API<br/><input name="api_base_url" value="{html.escape(api_base_url)}" /></label>
          <label>API ключ<br/><input name="api_key" value="{html.escape(api_key)}" /></label>
        </div>
        <div class="row cols-2" style="margin-top:10px">
          <label>SERVER_NAME (опционально)<br/><input name="server_name" value="{html.escape(server_name)}" placeholder="my-server-01" /></label>
          <label>AGENT_DISK_PATH (путь диска)<br/><input name="disk_path" value="{html.escape(disk_path)}" /></label>
        </div>
        <div style="margin-top:10px">
          <button class="btn" type="submit">Сгенерировать</button>
        </div>
      </form>
    </section>

    <section class="card" style="margin-top:12px">
      <h2>Готовые переменные окружения</h2>
      <pre><code>set API_BASE_URL={html.escape(api_base_url)}
set API_KEY={html.escape(api_key)}
{server_name_line}set AGENT_DISK_PATH={html.escape(disk_path)}</code></pre>
      <div style="margin-top:10px">
        <a class="pill" href="/ui/agent-config/env?api_base_url={html.escape(api_base_url)}&api_key={html.escape(api_key)}&server_name={html.escape(server_name)}&disk_path={html.escape(disk_path)}">Скачать как .env</a>
      </div>
    </section>
    """
    return _layout("Конфиг агента", body)


@router.get("/agent-config/env", response_class=PlainTextResponse)
def agent_config_env(
    api_base_url: str = "http://localhost:8080",
    api_key: str = "dev-key-1",
    server_name: str = "",
    disk_path: str = "/",
) -> str:
    lines = [
        f"API_BASE_URL={api_base_url}",
        f"API_KEY={api_key}",
        f"AGENT_DISK_PATH={disk_path}",
    ]
    if server_name.strip():
        lines.insert(2, f"SERVER_NAME={server_name}")
    return "\n".join(lines) + "\n"

