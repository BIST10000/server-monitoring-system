from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.models import AlertEvent, AlertRule, Heartbeat, MetricPoint, Server
from app.settings import settings


def get_server_by_name(db: Session, name: str) -> Server | None:
    return db.scalar(select(Server).where(Server.name == name))


def create_server(db: Session, *, name: str, environment: str, labels: dict) -> Server:
    srv = Server(name=name, environment=environment, labels=labels)
    db.add(srv)
    db.commit()
    db.refresh(srv)
    return srv


def list_servers(db: Session, *, environment: str | None = None) -> list[Server]:
    stmt = select(Server).order_by(Server.created_at.desc())
    if environment:
        stmt = stmt.where(Server.environment == environment)
    return list(db.scalars(stmt).all())


def create_heartbeat(db: Session, *, server: Server, agent_version: str | None, payload: dict) -> Heartbeat:
    hb = Heartbeat(server_id=server.id, agent_version=agent_version, payload=payload)
    db.add(hb)
    db.commit()
    db.refresh(hb)
    return hb


def create_metric_point(
    db: Session, *, server: Server, name: str, value: float, tags: dict, ts: datetime
) -> MetricPoint:
    mp = MetricPoint(server_id=server.id, name=name, value=value, tags=tags, ts=ts)
    db.add(mp)
    db.commit()
    db.refresh(mp)
    return mp


def list_metric_points(
    db: Session,
    *,
    server_id: str | None = None,
    name: str | None = None,
    since: datetime | None = None,
    limit: int = 200,
) -> list[MetricPoint]:
    stmt = select(MetricPoint).order_by(desc(MetricPoint.ts)).limit(limit)
    if server_id:
        stmt = stmt.where(MetricPoint.server_id == server_id)
    if name:
        stmt = stmt.where(MetricPoint.name == name)
    if since:
        stmt = stmt.where(MetricPoint.ts >= since)
    return list(db.scalars(stmt).all())


def create_alert_rule(
    db: Session,
    *,
    name: str,
    metric_name: str,
    comparator: str,
    threshold: float,
    window_seconds: int,
    enabled: bool,
    labels: dict,
) -> AlertRule:
    rule = AlertRule(
        name=name,
        metric_name=metric_name,
        comparator=comparator,
        threshold=threshold,
        window_seconds=window_seconds,
        enabled=enabled,
        labels=labels,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_alert_rules(db: Session) -> list[AlertRule]:
    return list(db.scalars(select(AlertRule).order_by(AlertRule.created_at.desc())).all())


def delete_alert_rule(db: Session, *, rule_id: str) -> bool:
    rule = db.scalar(select(AlertRule).where(AlertRule.id == rule_id))
    if rule is None:
        return False
    db.delete(rule)
    db.commit()
    return True


def list_alert_events(
    db: Session,
    *,
    status: str | None = None,
    server_id: str | None = None,
    limit: int = 200,
) -> list[AlertEvent]:
    stmt = select(AlertEvent).order_by(AlertEvent.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(AlertEvent.status == status)
    if server_id:
        stmt = stmt.where(AlertEvent.server_id == server_id)
    return list(db.scalars(stmt).all())


def set_alert_event_status(db: Session, *, alert_id: str, status: str) -> bool:
    evt = db.scalar(select(AlertEvent).where(AlertEvent.id == alert_id))
    if evt is None:
        return False
    evt.status = status
    db.commit()
    return True


def get_alert_event_by_id(db: Session, *, alert_id: str) -> AlertEvent | None:
    return db.scalar(select(AlertEvent).where(AlertEvent.id == alert_id))


def evaluate_alert_rules(db: Session) -> int:
    now = datetime.now(timezone.utc)
    rules = list(db.scalars(select(AlertRule).where(AlertRule.enabled.is_(True))).all())
    created = 0

    for rule in rules:
        window_start = now - timedelta(seconds=rule.window_seconds)
        avg_stmt = (
            select(MetricPoint.server_id, func.avg(MetricPoint.value))
            .where(and_(MetricPoint.name == rule.metric_name, MetricPoint.ts >= window_start))
            .group_by(MetricPoint.server_id)
        )
        for server_id, avg_value in db.execute(avg_stmt).all():
            if avg_value is None:
                continue

            is_violation = _compare(float(avg_value), rule.comparator, float(rule.threshold))
            if not is_violation:
                continue

            evt = AlertEvent(
                rule_id=rule.id,
                server_id=server_id,
                status="firing",
                message=f"{rule.metric_name} avg {avg_value:.2f} {rule.comparator} {rule.threshold} (violated)",
                details={"avg": float(avg_value), "window_seconds": rule.window_seconds},
            )
            db.add(evt)
            created += 1

    db.commit()
    return created


def purge_old_metrics(db: Session) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.metric_retention_days)
    res = db.execute(select(MetricPoint.id).where(MetricPoint.ts < cutoff).limit(5000)).all()
    ids = [r[0] for r in res]
    if not ids:
        return 0
    db.query(MetricPoint).filter(MetricPoint.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return len(ids)


def _compare(value: float, comparator: str, threshold: float) -> bool:
    if comparator == ">":
        return value > threshold
    if comparator == ">=":
        return value >= threshold
    if comparator == "<":
        return value < threshold
    if comparator == "<=":
        return value <= threshold
    raise ValueError(f"Unsupported comparator: {comparator}")

