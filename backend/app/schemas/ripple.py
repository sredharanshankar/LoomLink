from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ForecastSnapshotOut(BaseModel):
    id: uuid.UUID
    state_version: int
    computed_at: dt.datetime
    forecast: dict[str, Any]
    trigger_event_id: int | None = None


class OrderHealthOut(BaseModel):
    health: str
    slack_minutes: int | None
    predicted_dispatch_at: dt.datetime | None
    confidence_minutes: int
    is_estimate: bool = True


class RippleFixOut(BaseModel):
    id: uuid.UUID
    rank: int
    kind: str
    title_key: str
    params: dict[str, Any]
    actions: list[dict[str, Any]]
    orders_on_time: int
    orders_total: int
    total_late_minutes: int
    extra_cost_paise: int
    changes_count: int
    explanation_key: str | None
    explanation_params: dict[str, Any]
    applied_at: dt.datetime | None
    applied_by: uuid.UUID | None


class RippleEventOut(BaseModel):
    id: uuid.UUID
    code: str
    trigger_event_id: int | None
    trigger_kind: str
    event_type: str = ""
    title_key: str
    title: str = ""
    summary: str = ""
    severity: str = "medium"
    params: dict[str, Any]
    affected_orders: list[dict[str, Any]]
    affected_order_codes: list[str] = Field(default_factory=list)
    at_risk_paise: int
    at_risk_breakdown: dict[str, Any]
    status: str
    snapshot_id: uuid.UUID | None
    resolved_fix_id: uuid.UUID | None
    resolved_by: uuid.UUID | None
    resolved_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime | None
    fixes: list[RippleFixOut] = Field(default_factory=list)


class RippleEventListOut(BaseModel):
    items: list[RippleEventOut]
    total: int


class ApplyFixIn(BaseModel):
    expected_state_version: int = Field(ge=0)


class DismissRippleIn(BaseModel):
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason must not be blank")
        return value.strip()


class WhatIfScenario(BaseModel):
    kind: Literal["breakdown", "yarn_delay", "rush_order", "absence"]
    params: dict[str, Any] = Field(default_factory=dict)


class WhatIfIn(BaseModel):
    scenario: WhatIfScenario


class WhatIfOut(BaseModel):
    scenario_kind: str
    before: dict[str, Any]
    after: dict[str, Any]
    diff: dict[str, Any]
    at_risk: dict[str, Any]
    fixes: list[dict[str, Any]]
    is_estimate: bool = True


class PromiseDateIn(BaseModel):
    buyer_id: uuid.UUID
    fabric_type_id: uuid.UUID
    quantity_cm: int = Field(gt=0)
    requested_date: dt.date | None = None
    priority: Literal["normal", "high", "rush"] = "normal"


class PromiseConditionOut(BaseModel):
    key: str
    params: dict[str, Any]


class PromiseImpactOut(BaseModel):
    order_id: str
    code: str
    slack_delta_minutes: int | None
    newly_late: bool


class PrioritisedPromiseOut(BaseModel):
    dispatch_date: dt.date | None
    impacts: list[PromiseImpactOut]


class PromiseDateOut(BaseModel):
    earliest_dispatch_date: dt.date | None
    limiting_factor: str
    conditions: list[PromiseConditionOut]
    if_prioritised: PrioritisedPromiseOut
    suggested_quote_key: str
    params: dict[str, Any]
    is_estimate: bool = True


class IdleHunterSuggestionOut(BaseModel):
    machine: dict[str, Any]
    job: dict[str, Any]
    order: dict[str, Any]
    gain_minutes: int
    reason_key: str
    params: dict[str, Any]
