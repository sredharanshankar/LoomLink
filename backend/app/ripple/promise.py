from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.ripple.forecast import forecast
from app.ripple.model import JobState, JsonMixin, MillState, OrderState, YarnState

DRAFT_ORDER_ID = "__promise_draft__"


@dataclass(frozen=True)
class PromiseCondition(JsonMixin):
    key: str
    params: Mapping[str, Any]


@dataclass(frozen=True)
class PromiseImpact(JsonMixin):
    order_id: str
    code: str
    slack_delta_minutes: int | None
    newly_late: bool


@dataclass(frozen=True)
class PrioritisedPromise(JsonMixin):
    dispatch_date: date | None
    impacts: tuple[PromiseImpact, ...]


@dataclass(frozen=True)
class PromiseResult(JsonMixin):
    earliest_dispatch_date: date | None
    limiting_factor: str
    conditions: tuple[PromiseCondition, ...]
    if_prioritised: PrioritisedPromise
    suggested_quote_key: str
    params: Mapping[str, Any]
    is_estimate: bool = True


def _value(draft: object, key: str, default: Any = None) -> Any:
    if isinstance(draft, Mapping):
        return draft.get(key, default)
    return getattr(draft, key, default)


def build_hypothetical_state(state: MillState, draft: object, priority: str) -> MillState:
    quantity_cm = int(_value(draft, "quantity_cm", 0))
    yarn_needed = int(_value(draft, "yarn_needed_g", _value(draft, "yarn_need_g", 0)))
    fabric_type_id = str(_value(draft, "fabric_type_id"))
    yarn_type_id = str(_value(draft, "yarn_type_id"))
    route = tuple(_value(draft, "route_stages", ("weaving", "dyeing", "finishing")))
    code = str(_value(draft, "code", "DRAFT"))
    due_at = state.now + timedelta(days=state.settings.horizon_days)
    order = OrderState(
        id=DRAFT_ORDER_ID,
        code=code,
        buyer_id=str(_value(draft, "buyer_id", "draft-buyer")),
        buyer_name=str(_value(draft, "buyer_name", "Draft buyer")),
        due_at=due_at,
        priority=priority,
        penalty_paise_per_day=int(_value(draft, "penalty_paise_per_day", 0)),
        quantity_cm=quantity_cm,
        fabric_type_id=fabric_type_id,
        yarn_type_id=yarn_type_id,
        yarn_needed_remaining_g=yarn_needed,
        status="confirmed",
        promised_date=None,
        rolls_pending_qc=0,
        production_done=False,
    )
    stage_quantities = _value(draft, "stage_quantities", {})
    jobs: list[JobState] = []
    for index, stage in enumerate(route, start=1):
        default_quantity = yarn_needed if stage == "spinning" else quantity_cm
        quantity = (
            int(stage_quantities.get(stage, default_quantity))
            if isinstance(stage_quantities, Mapping)
            else default_quantity
        )
        jobs.append(
            JobState(
                id=f"{DRAFT_ORDER_ID}:{stage}:{index}",
                code=f"{code}-{stage[:2].upper()}",
                order_id=DRAFT_ORDER_ID,
                stage=str(stage),
                seq=index,
                unit="g" if stage == "spinning" else "cm",
                fabric_type_id=fabric_type_id,
                remaining_qty=quantity,
                status="ready",
                machine_id=None,
                queue_position=None,
                is_running=False,
            )
        )
    return replace(state, orders=(*state.orders, order), jobs=(*state.jobs, *jobs))


def _quoted_date(instant: datetime | None, timezone_name: str) -> date | None:
    if instant is None:
        return None
    local = instant.astimezone(ZoneInfo(timezone_name))
    quoted = local.date()
    if local.hour >= 18:
        quoted += timedelta(days=1)
    return quoted


def _limiting_factor(result: object, hypothetical: MillState) -> str:
    order_result = next(item for item in result.orders if item.order_id == DRAFT_ORDER_ID)  # type: ignore[attr-defined]
    draft_job_ids = {item.id for item in hypothetical.jobs if item.order_id == DRAFT_ORDER_ID}
    if any(
        item.job_id in draft_job_ids and item.waiting_on == "yarn"
        for item in result.jobs  # type: ignore[attr-defined]
    ):
        return "yarn"
    if order_result.bottleneck is not None:
        if order_result.bottleneck.kind == "yarn":
            return "yarn"
        if order_result.bottleneck.kind == "machine":
            return f"machine:{order_result.bottleneck.ref}"
        if order_result.bottleneck.kind in {"stage", "predecessor"}:
            return f"stage:{order_result.bottleneck.ref}"
    if order_result.predicted_dispatch_at is None:
        draft_jobs = [item for item in hypothetical.jobs if item.order_id == DRAFT_ORDER_ID]
        job_results = {item.job_id: item for item in result.jobs}  # type: ignore[attr-defined]
        missing = next((item for item in draft_jobs if job_results[item.id].end_at is None), None)
        return f"stage:{missing.stage}" if missing is not None else "none"
    return "none"


def promise_date(state: MillState, draft: object, priority: str = "normal") -> PromiseResult:
    hypothetical = build_hypothetical_state(state, draft, priority)
    normal = forecast(hypothetical)
    draft_result = next(item for item in normal.orders if item.order_id == DRAFT_ORDER_ID)
    earliest = _quoted_date(draft_result.predicted_dispatch_at, state.settings.timezone)
    limiting = _limiting_factor(normal, hypothetical)
    conditions: list[PromiseCondition] = []
    if limiting == "yarn":
        no_yarn_orders = tuple(
            replace(item, yarn_needed_remaining_g=0) if item.id == DRAFT_ORDER_ID else item
            for item in hypothetical.orders
        )
        capacity_state = replace(hypothetical, orders=no_yarn_orders)
        capacity_forecast = forecast(capacity_state)
        route_jobs = sorted(
            (item for item in capacity_state.jobs if item.order_id == DRAFT_ORDER_ID),
            key=lambda item: item.seq,
        )
        first_job = next(
            (item for item in capacity_forecast.jobs if route_jobs and item.job_id == route_jobs[0].id),
            None,
        )
        needed_at = first_job.start_at if first_job is not None else None
        conditional_date: date | None = None
        if needed_at is not None:
            yarn_needed = next(
                item.yarn_needed_remaining_g for item in hypothetical.orders if item.id == DRAFT_ORDER_ID
            )
            yarn_type = next(item.yarn_type_id for item in hypothetical.orders if item.id == DRAFT_ORDER_ID)
            found = False
            conditional_yarn: list[YarnState] = []
            for item in hypothetical.yarn:
                if item.yarn_type_id == yarn_type:
                    conditional_yarn.append(
                        replace(
                            item,
                            arrivals=tuple(
                                sorted(
                                    (*item.arrivals, (needed_at, yarn_needed)),
                                    key=lambda arrival: arrival[0],
                                )
                            ),
                        )
                    )
                    found = True
                else:
                    conditional_yarn.append(item)
            if not found:
                conditional_yarn.append(YarnState(yarn_type, 0, ((needed_at, yarn_needed),)))
            conditional = forecast(replace(hypothetical, yarn=tuple(conditional_yarn)))
            conditional_order = next(item for item in conditional.orders if item.order_id == DRAFT_ORDER_ID)
            conditional_date = _quoted_date(conditional_order.predicted_dispatch_at, state.settings.timezone)
        conditions.append(
            PromiseCondition(
                key="ripple.promise.if_yarn_arrives",
                params={
                    "needed_by": needed_at.astimezone(ZoneInfo(state.settings.timezone)).date().isoformat()
                    if needed_at is not None
                    else None,
                    "dispatch_date": conditional_date.isoformat() if conditional_date is not None else None,
                },
            )
        )

    prioritised_state = build_hypothetical_state(state, draft, "rush")
    prioritised = forecast(prioritised_state)
    prioritised_draft = next(item for item in prioritised.orders if item.order_id == DRAFT_ORDER_ID)
    normal_by_id = {item.order_id: item for item in normal.orders if item.order_id != DRAFT_ORDER_ID}
    impacts: list[PromiseImpact] = []
    for item in prioritised.orders:
        if item.order_id == DRAFT_ORDER_ID or item.order_id not in normal_by_id:
            continue
        before = normal_by_id[item.order_id]
        delta = (
            None
            if before.slack_minutes is None or item.slack_minutes is None
            else item.slack_minutes - before.slack_minutes
        )
        newly_late = (
            before.slack_minutes is not None
            and before.slack_minutes >= 0
            and (item.slack_minutes is None or item.slack_minutes < 0)
        )
        if delta not in (None, 0) or newly_late:
            impacts.append(PromiseImpact(item.order_id, item.code, delta, newly_late))
    quote_params = {"date": earliest.isoformat() if earliest is not None else None}
    return PromiseResult(
        earliest_dispatch_date=earliest,
        limiting_factor=limiting,
        conditions=tuple(conditions),
        if_prioritised=PrioritisedPromise(
            dispatch_date=_quoted_date(prioritised_draft.predicted_dispatch_at, state.settings.timezone),
            impacts=tuple(sorted(impacts, key=lambda item: item.code)),
        ),
        suggested_quote_key="ripple.promise.quote" if earliest is not None else "ripple.promise.no_capacity",
        params=quote_params,
    )
