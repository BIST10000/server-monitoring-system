from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    environment: str = Field(default="prod", max_length=50)
    labels: dict = Field(default_factory=dict)


class ServerOut(BaseModel):
    id: uuid.UUID
    name: str
    environment: str
    labels: dict
    created_at: datetime


class HeartbeatIn(BaseModel):
    server_name: str = Field(min_length=1, max_length=200)
    agent_version: str | None = Field(default=None, max_length=50)
    payload: dict = Field(default_factory=dict)


class HeartbeatOut(BaseModel):
    id: uuid.UUID
    server_id: uuid.UUID
    agent_version: str | None
    payload: dict
    created_at: datetime


class MetricPointIn(BaseModel):
    server_name: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    value: float
    tags: dict = Field(default_factory=dict)
    ts: datetime


class MetricPointOut(BaseModel):
    id: uuid.UUID
    server_id: uuid.UUID
    name: str
    value: float
    tags: dict
    ts: datetime
    created_at: datetime


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    metric_name: str = Field(min_length=1, max_length=200)
    comparator: str = Field(pattern=r"^(>=|<=|>|<)$")
    threshold: float
    window_seconds: int = Field(default=60, ge=10, le=86400)
    enabled: bool = True
    labels: dict = Field(default_factory=dict)


class AlertRuleOut(BaseModel):
    id: uuid.UUID
    name: str
    metric_name: str
    comparator: str
    threshold: float
    window_seconds: int
    enabled: bool
    labels: dict
    created_at: datetime


class AlertEventOut(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID
    server_id: uuid.UUID | None
    status: str
    message: str
    details: dict
    created_at: datetime

