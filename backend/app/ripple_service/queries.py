from __future__ import annotations

import datetime as dt
import uuid
from collections import defaultdict
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import now
from app.models.identity import MillSettings
from app.models.ripple import LeakEntry, RippleEvent, RippleFix, RippleSnapshot
from app.models.sales import Buyer, FabricType, RouteStep
from app.ripple.promise import promise_date
from app.ripple.whatif import what_if

from .engine_runner import latest_snapshot, recompute
from .state_loader import load_mill_state


def snapshot_to_dict(row: RippleSnapshot) -> dict[str, Any]:
    return {
        "id": row.id,
        "state_version": row.state_version,
        "computed_at": row.computed_at,
        "forecast": row.forecast or {},
        "trigger_event_id": row.trigger_event_id,
    }


def get_latest_forecast(session: Session) -> dict[str, Any]:
    return snapshot_to_dict(latest_snapshot(session) or recompute(session))


def _health_from_order(order: dict, *, is_estimate: bool) -> dict:
    return {
        "health": order.get("health"),
        "slack_minutes": order.get("slack_minutes"),
        "predicted_dispatch_at": order.get("predicted_dispatch_at"),
        "confidence_minutes": order.get("confidence_minutes", 0),
        "is_estimate": is_estimate,
    }


def get_order_health(session: Session, order_id: uuid.UUID) -> dict | None:
    row = latest_snapshot(session)
    if row is None or not row.forecast:
        return None
    for order in row.forecast.get("orders", []):
        if str(order.get("order_id")) == str(order_id):
            return _health_from_order(order, is_estimate=bool(row.forecast.get("is_estimate", True)))
    return None


def get_orders_health(session: Session, order_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    requested = {str(item): item for item in order_ids}
    row = latest_snapshot(session)
    if row is None or not row.forecast:
        return {}
    return {
        requested[str(order["order_id"])]: _health_from_order(
            order, is_estimate=bool(row.forecast.get("is_estimate", True))
        )
        for order in row.forecast.get("orders", [])
        if str(order.get("order_id")) in requested
    }


def get_open_ripple_count(session: Session) -> int:
    return int(
        session.scalar(select(func.count()).select_from(RippleEvent).where(RippleEvent.status == "open")) or 0
    )


def get_leak_today(session: Session) -> dict:
    settings = session.scalar(select(MillSettings).limit(1))
    today = now().astimezone(ZoneInfo(settings.timezone if settings else "Asia/Kolkata")).date()
    by_category: dict[str, int] = defaultdict(int)
    for category, amount in session.execute(
        select(LeakEntry.category, func.coalesce(func.sum(LeakEntry.amount_paise), 0))
        .where(LeakEntry.date == today)
        .group_by(LeakEntry.category)
    ):
        by_category[getattr(category, "value", category)] = int(amount)
    return {"total_paise": sum(by_category.values()), "by_category": dict(by_category)}


def fix_to_dict(row: RippleFix) -> dict[str, Any]:
    return {
        "id": row.id,
        "rank": row.rank,
        "kind": row.kind,
        "title_key": row.title_key,
        "params": row.params or {},
        "actions": row.actions or [],
        "orders_on_time": row.orders_on_time,
        "orders_total": row.orders_total,
        "total_late_minutes": row.total_late_minutes,
        "extra_cost_paise": row.extra_cost_paise,
        "changes_count": row.changes_count,
        "explanation_key": row.explanation_key,
        "explanation_params": row.explanation_params or {},
        "applied_at": row.applied_at,
        "applied_by": row.applied_by,
    }


def event_to_dict(session: Session, row: RippleEvent, *, include_fixes: bool = True) -> dict[str, Any]:
    fixes = (
        list(
            session.scalars(
                select(RippleFix).where(RippleFix.ripple_event_id == row.id).order_by(RippleFix.rank)
            )
        )
        if include_fixes
        else []
    )
    trigger_kind = getattr(row.trigger_kind, "value", row.trigger_kind) or ""
    params = row.params or {}
    severity = params.get("severity", "medium")
    affected = row.affected_orders or []
    affected_order_codes = [o.get("order_code", "") for o in affected if isinstance(o, dict)]
    title_key = row.title_key or trigger_kind
    machine = params.get("machine_code", "")
    title = title_key.replace("ripple.", "").replace("_", " ").title()
    if machine:
        title = f"{machine} — {title}"
    summary = f"Affected orders: {', '.join(affected_order_codes) if affected_order_codes else 'none'}"
    return {
        "id": row.id,
        "code": row.code,
        "event_type": trigger_kind,
        "trigger_event_id": row.trigger_event_id,
        "trigger_kind": trigger_kind,
        "title": title,
        "title_key": row.title_key,
        "summary": summary,
        "severity": severity,
        "params": params,
        "affected_orders": affected,
        "affected_order_codes": affected_order_codes,
        "at_risk_paise": row.at_risk_paise,
        "at_risk_breakdown": row.at_risk_breakdown or {},
        "status": getattr(row.status, "value", row.status),
        "snapshot_id": row.snapshot_id,
        "resolved_fix_id": row.resolved_fix_id,
        "resolved_by": row.resolved_by,
        "resolved_at": row.resolved_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "fixes": [fix_to_dict(item) for item in fixes],
    }


def list_events(session: Session, status: str | None = None) -> dict[str, Any]:
    statement = select(RippleEvent)
    if status is not None:
        statement = statement.where(RippleEvent.status == status)
    rows = list(session.scalars(statement.order_by(RippleEvent.created_at.desc())))
    return {"items": [event_to_dict(session, row, include_fixes=False) for row in rows], "total": len(rows)}


def get_event(session: Session, event_id: uuid.UUID) -> dict[str, Any]:
    row = session.get(RippleEvent, event_id)
    if row is None:
        raise AppError("NOT_FOUND", "Ripple event not found.")
    return event_to_dict(session, row)


def run_what_if(session: Session, scenario: dict[str, Any]) -> dict[str, Any]:
    try:
        return what_if(
            load_mill_state(session), {"kind": scenario["kind"], **scenario.get("params", {})}
        ).to_dict()
    except (KeyError, TypeError, ValueError) as exc:
        raise AppError("VALIDATION_ERROR", str(exc), status=400) from exc


def calculate_promise_date(
    session: Session,
    *,
    buyer_id: uuid.UUID,
    fabric_type_id: uuid.UUID,
    quantity_cm: int,
    requested_date: dt.date | None,
    priority: str,
) -> dict[str, Any]:
    buyer, fabric = session.get(Buyer, buyer_id), session.get(FabricType, fabric_type_id)
    if buyer is None or fabric is None:
        raise AppError("NOT_FOUND", "Buyer or fabric type not found.")
    stages = (
        tuple(
            session.scalars(
                select(RouteStep.stage)
                .where(RouteStep.template_id == fabric.route_template_id)
                .order_by(RouteStep.seq)
            )
        )
        if fabric.route_template_id
        else ("weaving", "dyeing", "finishing")
    )
    draft = {
        "code": "DRAFT",
        "buyer_id": str(buyer.id),
        "buyer_name": buyer.name,
        "fabric_type_id": str(fabric.id),
        "quantity_cm": quantity_cm,
        "yarn_type_id": str(fabric.yarn_type_id),
        "yarn_needed_g": quantity_cm * fabric.yarn_g_per_100m // 10_000,
        "route_stages": stages,
        "requested_date": requested_date.isoformat() if requested_date else None,
        "penalty_paise_per_day": buyer.default_late_penalty_paise_per_day,
    }
    return promise_date(load_mill_state(session), draft, priority).to_dict()


def get_idle_hunter(session: Session) -> list[dict[str, Any]]:  # noqa: ARG001
    return []
