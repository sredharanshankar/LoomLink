"""Ripple & intelligence endpoints — owned by Lane B."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.deps import get_db, require_permission
from app.ripple_service import apply as apply_service
from app.ripple_service import engine_runner, queries
from app.schemas.ripple import (
    ApplyFixIn,
    DismissRippleIn,
    ForecastSnapshotOut,
    IdleHunterSuggestionOut,
    OrderHealthOut,
    PromiseDateIn,
    PromiseDateOut,
    RippleEventListOut,
    RippleEventOut,
    WhatIfIn,
    WhatIfOut,
)

router = APIRouter()


@router.get("/ripple/forecast", response_model=ForecastSnapshotOut)
def get_forecast(user=Depends(require_permission("ripple.view")), db: Session = Depends(get_db)):
    return queries.get_latest_forecast(db)


@router.post("/ripple/recompute", response_model=ForecastSnapshotOut)
def force_recompute(user=Depends(require_permission("ripple.manage")), db: Session = Depends(get_db)):
    row = engine_runner.recompute(db, {"type": "ripple.manual", "payload": {"actor_id": user.get("id")}})
    return queries.snapshot_to_dict(row)


@router.get("/ripple/orders/{id}/health", response_model=OrderHealthOut)
def order_health(
    id: uuid.UUID, user=Depends(require_permission("orders.view")), db: Session = Depends(get_db)
):
    result = queries.get_order_health(db, id)
    if result is None:
        raise AppError("NOT_FOUND", "No forecast exists for this order.")
    return result


@router.get("/ripple/events", response_model=RippleEventListOut)
def list_events(
    status: Literal["open", "resolved", "dismissed"] | None = Query(None),
    user=Depends(require_permission("ripple.view")),
    db: Session = Depends(get_db),
):
    return queries.list_events(db, status)


@router.get("/ripple/events/{id}", response_model=RippleEventOut)
def get_event(id: uuid.UUID, user=Depends(require_permission("ripple.view")), db: Session = Depends(get_db)):
    return queries.get_event(db, id)


@router.post("/ripple/events/{id}/fixes/{fix_id}/apply", response_model=RippleEventOut)
def apply_fix(
    id: uuid.UUID,
    fix_id: uuid.UUID,
    body: ApplyFixIn,
    user=Depends(require_permission("ripple.apply")),
    db: Session = Depends(get_db),
):
    return queries.event_to_dict(
        db, apply_service.apply_fix(db, id, fix_id, body.expected_state_version, user)
    )


@router.post("/ripple/events/{id}/dismiss", response_model=RippleEventOut)
def dismiss_event(
    id: uuid.UUID,
    body: DismissRippleIn,
    user=Depends(require_permission("ripple.apply")),
    db: Session = Depends(get_db),
):
    return queries.event_to_dict(db, apply_service.dismiss_event(db, id, body.reason, user))


@router.post("/ripple/what-if", response_model=WhatIfOut)
def what_if(body: WhatIfIn, user=Depends(require_permission("ripple.view")), db: Session = Depends(get_db)):
    return queries.run_what_if(db, body.scenario.model_dump())


@router.post("/ripple/promise-date", response_model=PromiseDateOut)
def promise_date(
    body: PromiseDateIn,
    user=Depends(require_permission("orders.manage")),
    db: Session = Depends(get_db),
):
    return queries.calculate_promise_date(db, **body.model_dump())


@router.get("/ripple/idle-hunter", response_model=list[IdleHunterSuggestionOut])
def idle_hunter(user=Depends(require_permission("ripple.view")), db: Session = Depends(get_db)):
    return queries.get_idle_hunter(db)
