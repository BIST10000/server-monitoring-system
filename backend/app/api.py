from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.db import get_db
from app.schemas import (
    AlertEventOut,
    AlertRuleCreate,
    AlertRuleOut,
    HeartbeatIn,
    HeartbeatOut,
    MetricPointIn,
    MetricPointOut,
    ServerCreate,
    ServerOut,
)
from app.security import require_api_key

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])


@router.post("/servers", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
def create_server(payload: ServerCreate, db: Session = Depends(get_db)) -> ServerOut:
    try:
        srv = crud.create_server(db, name=payload.name, environment=payload.environment, labels=payload.labels)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Server with this name already exists")
    return ServerOut.model_validate(srv, from_attributes=True)


@router.get("/servers", response_model=list[ServerOut])
def list_servers(
    environment: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ServerOut]:
    items = crud.list_servers(db, environment=environment)
    return [ServerOut.model_validate(x, from_attributes=True) for x in items]


@router.post("/heartbeats", response_model=HeartbeatOut, status_code=status.HTTP_201_CREATED)
def ingest_heartbeat(payload: HeartbeatIn, db: Session = Depends(get_db)) -> HeartbeatOut:
    srv = crud.get_server_by_name(db, payload.server_name)
    if srv is None:
        srv = crud.create_server(db, name=payload.server_name, environment="prod", labels={})
    hb = crud.create_heartbeat(db, server=srv, agent_version=payload.agent_version, payload=payload.payload)
    return HeartbeatOut.model_validate(hb, from_attributes=True)


@router.post("/metrics", response_model=MetricPointOut, status_code=status.HTTP_201_CREATED)
def ingest_metric(payload: MetricPointIn, db: Session = Depends(get_db)) -> MetricPointOut:
    srv = crud.get_server_by_name(db, payload.server_name)
    if srv is None:
        srv = crud.create_server(db, name=payload.server_name, environment="prod", labels={})
    mp = crud.create_metric_point(db, server=srv, name=payload.name, value=payload.value, tags=payload.tags, ts=payload.ts)
    return MetricPointOut.model_validate(mp, from_attributes=True)


@router.get("/metrics", response_model=list[MetricPointOut])
def list_metrics(
    server_id: str | None = Query(default=None),
    name: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> list[MetricPointOut]:
    items = crud.list_metric_points(db, server_id=server_id, name=name, since=since, limit=limit)
    return [MetricPointOut.model_validate(x, from_attributes=True) for x in items]


@router.post("/alert-rules", response_model=AlertRuleOut, status_code=status.HTTP_201_CREATED)
def create_alert_rule(payload: AlertRuleCreate, db: Session = Depends(get_db)) -> AlertRuleOut:
    try:
        rule = crud.create_alert_rule(db, **payload.model_dump())
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Alert rule with this name already exists")
    return AlertRuleOut.model_validate(rule, from_attributes=True)


@router.get("/alert-rules", response_model=list[AlertRuleOut])
def list_alert_rules(db: Session = Depends(get_db)) -> list[AlertRuleOut]:
    items = crud.list_alert_rules(db)
    return [AlertRuleOut.model_validate(x, from_attributes=True) for x in items]


@router.delete("/alert-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert_rule(rule_id: str, db: Session = Depends(get_db)) -> Response:
    try:
        UUID(rule_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    deleted = crud.delete_alert_rule(db, rule_id=rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/alerts/evaluate", response_model=dict)
def evaluate_alerts(db: Session = Depends(get_db)) -> dict:
    created = crud.evaluate_alert_rules(db)
    purged = crud.purge_old_metrics(db)
    return {"created_alert_events": created, "purged_metrics": purged, "ts": datetime.now(timezone.utc).isoformat()}


@router.get("/alerts", response_model=list[AlertEventOut])
def list_alerts(
    status_: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=200, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> list[AlertEventOut]:
    items = crud.list_alert_events(db, status=status_, limit=limit)
    return [AlertEventOut.model_validate(x, from_attributes=True) for x in items]


@router.post("/alerts/{alert_id}/resolve", response_model=AlertEventOut)
def resolve_alert(alert_id: str, db: Session = Depends(get_db)) -> AlertEventOut:
    try:
        UUID(alert_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Alert not found")
    updated = crud.set_alert_event_status(db, alert_id=alert_id, status="resolved")
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")
    item = crud.get_alert_event_by_id(db, alert_id=alert_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertEventOut.model_validate(item, from_attributes=True)

