"""Seed mill_settings and demo users for a fresh DB."""
from __future__ import annotations
import uuid
import datetime as dt
from sqlalchemy.orm import Session
from app.core.security import hash_password, hash_pin
from app.core.time import now


DEMO_MILL = {
    "mill_name": "Everest Textile Mills",
    "timezone": "Asia/Kolkata",
    "gst_default_bp": 500,
    "overtime_multiplier_bp": 15000,
    "order_tolerance_bp": 200,
    "aged_stock_days": 7,
    "health_amber_minutes": 1440,
    "ripple_slip_threshold_minutes": 60,
    "qc_buffer_minutes": 30,
    "dispatch_buffer_minutes": 30,
}

DEMO_USERS = [
    {"name": "Owner", "employee_code": "OWN-001", "role": "owner", "password": "demo1234", "pin": "100001"},
    {"name": "Manager", "employee_code": "MGR-001", "role": "manager", "password": "demo1234", "pin": "200002"},
    {"name": "Storekeeper", "employee_code": "STK-001", "role": "storekeeper", "password": "demo1234", "pin": "300003"},
    {"name": "Operator A", "employee_code": "OPR-001", "role": "operator", "password": None, "pin": "400004"},
    {"name": "QC Inspector", "employee_code": "QCI-001", "role": "qc_inspector", "password": "demo1234", "pin": "500005"},
    {"name": "Dispatch", "employee_code": "DSP-001", "role": "dispatch", "password": "demo1234", "pin": "600006"},
    {"name": "Accounts", "employee_code": "ACC-001", "role": "accounts", "password": "demo1234", "pin": "700007"},
    {"name": "Buyer Demo", "employee_code": "BYR-001", "role": "buyer", "password": "demo1234", "pin": None},
]

DEMO_SHIFTS = [
    {"code": "A", "name": "Morning", "start_time": "06:00", "end_time": "14:00", "break_minutes": 30},
    {"code": "B", "name": "Afternoon", "start_time": "14:00", "end_time": "22:00", "break_minutes": 30},
    {"code": "C", "name": "Night (OT)", "start_time": "22:00", "end_time": "06:00", "break_minutes": 30, "is_overtime": True},
]

DEMO_DEFECT_CODES = [
    {"code": "HOLE", "label_en": "Hole", "default_severity": "critical"},
    {"code": "COLOUR_MISMATCH", "label_en": "Colour Mismatch", "default_severity": "major"},
    {"code": "UNEVEN_WEAVE", "label_en": "Uneven Weave", "default_severity": "minor"},
    {"code": "STAIN", "label_en": "Stain", "default_severity": "major"},
    {"code": "WIDTH_DEVIATION", "label_en": "Width Deviation", "default_severity": "minor"},
    {"code": "OTHER", "label_en": "Other", "default_severity": "minor"},
]


def seed_base(session: Session) -> None:
    from sqlalchemy import text

    # Mill settings (single row)
    exists = session.execute(text("SELECT COUNT(*) FROM mill_settings")).scalar()
    if not exists:
        session.execute(text("""
            INSERT INTO mill_settings (
                mill_name, timezone, gst_default_bp, overtime_multiplier_bp,
                order_tolerance_bp, aged_stock_days, health_amber_minutes,
                ripple_slip_threshold_minutes, qc_buffer_minutes, dispatch_buffer_minutes,
                rework_cost_paise_per_m, rework_minutes_per_roll, qc_packing_paise_per_roll,
                overhead_paise_per_m, state_version, created_at
            ) VALUES (
                :mill_name, :tz, :gst, :ot_mult, :tol, :aged, :health_amber,
                :ripple_slip, :qc_buf, :dsp_buf, 0, 0, 0, 0, 0, :now
            )
        """), {
            "mill_name": DEMO_MILL["mill_name"],
            "tz": DEMO_MILL["timezone"],
            "gst": DEMO_MILL["gst_default_bp"],
            "ot_mult": DEMO_MILL["overtime_multiplier_bp"],
            "tol": DEMO_MILL["order_tolerance_bp"],
            "aged": DEMO_MILL["aged_stock_days"],
            "health_amber": DEMO_MILL["health_amber_minutes"],
            "ripple_slip": DEMO_MILL["ripple_slip_threshold_minutes"],
            "qc_buf": DEMO_MILL["qc_buffer_minutes"],
            "dsp_buf": DEMO_MILL["dispatch_buffer_minutes"],
            "now": now(),
        })

    # Shifts
    for s in DEMO_SHIFTS:
        session.execute(text("""
            INSERT INTO shifts (code, name, start_time, end_time, break_minutes, is_overtime, created_at)
            VALUES (:code, :name, :start, :end, :break_m, :ot, :now)
            ON CONFLICT (code) DO NOTHING
        """), {
            "code": s["code"], "name": s["name"],
            "start": s["start_time"], "end": s["end_time"],
            "break_m": s.get("break_minutes", 30),
            "ot": s.get("is_overtime", False),
            "now": now(),
        })

    # Defect codes
    for d in DEMO_DEFECT_CODES:
        session.execute(text("""
            INSERT INTO defect_codes (id, code, label_en, default_severity, created_at)
            VALUES (gen_random_uuid(), :code, :label, :sev, :now)
            ON CONFLICT (code) DO NOTHING
        """), {"code": d["code"], "label": d["label_en"], "sev": d["default_severity"], "now": now()})

    # Users
    for u in DEMO_USERS:
        existing = session.execute(
            text("SELECT id FROM users WHERE employee_code = :code"),
            {"code": u["employee_code"]},
        ).fetchone()
        if existing:
            continue
        uid = str(uuid.uuid4())
        session.execute(text("""
            INSERT INTO users (id, employee_code, name, role, password_hash, pin_hash,
                               preferred_language, is_active, created_at)
            VALUES (:id, :code, :name, :role, :pw, :pin, 'en', true, :now)
        """), {
            "id": uid,
            "code": u["employee_code"],
            "name": u["name"],
            "role": u["role"],
            "pw": hash_password(u["password"]) if u.get("password") else None,
            "pin": hash_pin(u["pin"]) if u.get("pin") else None,
            "now": now(),
        })