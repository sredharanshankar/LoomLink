"""Demo convenience endpoints — only mounted when DEMO_MODE=true."""
from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.deps import require_permission, get_db

router = APIRouter()


@router.post("/demo/reset")
def demo_reset(
    user=Depends(require_permission("demo.reset")),
    db=Depends(get_db),
):
    """
    Reset the mill to demo state D 11:00.
    Clears scenario-specific data and re-seeds via scenario_demo.run().
    """
    # Delete in FK-safe order (children before parents)
    for tbl in [
        "ripple_fixes",
        "ripple_snapshots",
        "ripple_events",
        "leak_entries",
        "machine_events",
        "job_operator_sessions",
        "job_progress_logs",
        "job_material_consumption",
        "wip_lots",
        "jobs",
        "inspection_defects",
        "inspections",
        "rolls",
        "dispatch_items",
        "dispatches",
        "invoice_lines",
        "invoices",
        "payment_allocations",
        "payments_received",
        "stock_reservations",
        "stock_movements",
        "yarn_batches",
        "order_status_history",
        "orders",
        "attendance",
        "domain_events",
    ]:
        db.execute(text(f"DELETE FROM {tbl}"))

    # Reset all machines to idle
    db.execute(text("""
        UPDATE machines SET status = 'idle', current_job_id = NULL,
            status_changed_at = NOW(), updated_at = NOW()
    """))
    db.commit()

    # Re-run scenario seed
    from app.seed import scenario_demo
    scenario_demo.run(db)
    db.commit()

    return {"status": "reset", "message": "Mill reset to demo state D 11:00"}
