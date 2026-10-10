"""Seed mill_settings and demo users for a fresh DB."""
from __future__ import annotations
import json
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
    # SEED §1
    "qc_packing_paise_per_roll": 18000,
    "overhead_paise_per_m": 530,
    "rework_cost_paise_per_m": 1650,
    "machine_rate_paise_per_hour": {"spinning": 25000, "weaving": 45000, "dyeing": 60000, "finishing": 40000},
    "waste_norm_bp": {"spinning": 300, "weaving": 200, "dyeing": 150, "finishing": 100},
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

# SEED §2 — workers (wage_rate_paise = daily/hourly rate in paise)
DEMO_WORKERS = [
    {"code": "EMP-001", "name": "Ravi",    "skill_stages": ["weaving"],           "wage_type": "daily",  "wage_rate_paise": 80000, "piece_rate_paise_per_m": None, "default_shift": "A", "preferred_language": "te", "overtime_willing": False},
    {"code": "EMP-002", "name": "Murugan", "skill_stages": ["weaving"],           "wage_type": "daily",  "wage_rate_paise": 80000, "piece_rate_paise_per_m": None, "default_shift": "A", "preferred_language": "ta", "overtime_willing": False},
    {"code": "EMP-003", "name": "Lakshmi","skill_stages": ["weaving"],            "wage_type": "daily",  "wage_rate_paise": 78000, "piece_rate_paise_per_m": None, "default_shift": "A", "preferred_language": "ta", "overtime_willing": False},
    {"code": "EMP-004", "name": "Suresh",  "skill_stages": ["weaving"],           "wage_type": "daily",  "wage_rate_paise": 80000, "piece_rate_paise_per_m": None, "default_shift": "B", "preferred_language": "hi", "overtime_willing": False},
    {"code": "EMP-005", "name": "Priya",   "skill_stages": ["weaving"],           "wage_type": "daily",  "wage_rate_paise": 78000, "piece_rate_paise_per_m": None, "default_shift": "B", "preferred_language": "te", "overtime_willing": False},
    {"code": "EMP-006", "name": "Karthik", "skill_stages": ["weaving","finishing"],"wage_type": "daily",  "wage_rate_paise": 82000, "piece_rate_paise_per_m": None, "default_shift": "B", "preferred_language": "ta", "overtime_willing": False},
    {"code": "EMP-007", "name": "Anitha",  "skill_stages": ["dyeing"],            "wage_type": "daily",  "wage_rate_paise": 85000, "piece_rate_paise_per_m": None, "default_shift": "A", "preferred_language": "te", "overtime_willing": False},
    {"code": "EMP-008", "name": "Ganesh",  "skill_stages": ["dyeing"],            "wage_type": "daily",  "wage_rate_paise": 85000, "piece_rate_paise_per_m": None, "default_shift": "B", "preferred_language": "hi", "overtime_willing": False},
    {"code": "EMP-009", "name": "Selvi",   "skill_stages": ["finishing"],         "wage_type": "daily",  "wage_rate_paise": 76000, "piece_rate_paise_per_m": None, "default_shift": "A", "preferred_language": "ta", "overtime_willing": False},
    {"code": "EMP-010", "name": "Arjun",   "skill_stages": ["finishing"],         "wage_type": "piece",  "wage_rate_paise": 120,   "piece_rate_paise_per_m": 120,  "default_shift": "B", "preferred_language": "hi", "overtime_willing": False},
    {"code": "EMP-011", "name": "Meena",   "skill_stages": ["spinning"],          "wage_type": "daily",  "wage_rate_paise": 74000, "piece_rate_paise_per_m": None, "default_shift": "A", "preferred_language": "te", "overtime_willing": False},
    {"code": "EMP-012", "name": "Prakash", "skill_stages": ["weaving","dyeing"],  "wage_type": "hourly", "wage_rate_paise": 10500, "piece_rate_paise_per_m": None, "default_shift": "A", "preferred_language": "hi", "overtime_willing": True},
]

# SEED §3 — suppliers
DEMO_SUPPLIERS = [
    {"code": "SUP-001", "name": "Vel Spinners",           "payment_terms_days": 30, "yarn_codes": ["YT-COT-40S-WHT", "YT-COT-40S-BLU"]},
    {"code": "SUP-002", "name": "Annapoorna Yarns",       "payment_terms_days": 45, "yarn_codes": ["YT-PC-240S-GRY", "YT-COT-30S-NVY"]},
    {"code": "SUP-003", "name": "Kongu Cotton Traders",   "payment_terms_days": 30, "yarn_codes": ["YT-COT-40S-WHT", "YT-COT-30S-NVY"]},
]

# SEED §3 — yarn types
DEMO_YARN_TYPES = [
    {"code": "YT-COT-40S-WHT", "material": "cotton",      "count_label": "40s",  "colour": "white", "colour_hex": "#FFFFFF", "reorder_level_g": 150000, "standard_rate_paise_per_kg": 21000},
    {"code": "YT-COT-40S-BLU", "material": "cotton",      "count_label": "40s",  "colour": "blue",  "colour_hex": "#3B82F6", "reorder_level_g": 120000, "standard_rate_paise_per_kg": 24500},
    {"code": "YT-PC-240S-GRY", "material": "poly-cotton",  "count_label": "2/40s","colour": "grey",  "colour_hex": "#9CA3AF", "reorder_level_g": 100000, "standard_rate_paise_per_kg": 19000},
    {"code": "YT-COT-30S-NVY", "material": "cotton",      "count_label": "30s",  "colour": "navy",  "colour_hex": "#1E3A5F", "reorder_level_g": 100000, "standard_rate_paise_per_kg": 26000},
]

# SEED §4 — route templates
DEMO_ROUTES = [
    {"name": "R1", "description": "Weave → Dye → Finish", "steps": [
        {"seq": 1, "stage": "weaving",   "buffer_minutes": 60},
        {"seq": 2, "stage": "dyeing",    "buffer_minutes": 60},
        {"seq": 3, "stage": "finishing", "buffer_minutes": 30},
    ]},
    {"name": "R2", "description": "Spin → Weave → Dye → Finish", "steps": [
        {"seq": 1, "stage": "spinning",  "buffer_minutes": 60},
        {"seq": 2, "stage": "weaving",   "buffer_minutes": 60},
        {"seq": 3, "stage": "dyeing",    "buffer_minutes": 60},
        {"seq": 4, "stage": "finishing", "buffer_minutes": 30},
    ]},
]

# SEED §5 — fabric types
DEMO_FABRIC_TYPES = [
    {"code": "FAB-POP-BLU", "name": "Blue cotton poplin", "width_cm": 147, "gsm": 110, "colour": "blue",  "yarn_code": "YT-COT-40S-BLU", "yarn_g_per_100m": 14300, "route_name": "R1", "default_price_paise_per_m": 12500, "hsn_code": "5208"},
    {"code": "FAB-POP-GRY", "name": "Grey poplin",        "width_cm": 147, "gsm": 105, "colour": "grey",  "yarn_code": "YT-PC-240S-GRY", "yarn_g_per_100m": 13500, "route_name": "R1", "default_price_paise_per_m":  9800, "hsn_code": "5208"},
    {"code": "FAB-SHT-WHT", "name": "White sheeting",     "width_cm": 228, "gsm": 140, "colour": "white", "yarn_code": "YT-COT-40S-WHT", "yarn_g_per_100m": 26000, "route_name": "R1", "default_price_paise_per_m": 16000, "hsn_code": "5208"},
    {"code": "FAB-TWL-NVY", "name": "Navy twill",         "width_cm": 150, "gsm": 210, "colour": "navy",  "yarn_code": "YT-COT-30S-NVY", "yarn_g_per_100m": 27500, "route_name": "R2", "default_price_paise_per_m": 18500, "hsn_code": "5208"},
]

# SEED §6 — machines (WV-01/WV-02 can't do sheeting; WV-03 handles all)
DEMO_MACHINES = [
    {"code": "SP-01", "name": "Ring frame 1",        "stage": "spinning",  "floor_x": 2, "floor_y": 1, "fabric_codes": []},
    {"code": "WV-01", "name": "Air-jet loom 1",      "stage": "weaving",   "floor_x": 4, "floor_y": 1, "fabric_codes": ["FAB-POP-BLU", "FAB-POP-GRY", "FAB-TWL-NVY"]},
    {"code": "WV-02", "name": "Air-jet loom 2",      "stage": "weaving",   "floor_x": 4, "floor_y": 3, "fabric_codes": ["FAB-POP-BLU", "FAB-POP-GRY", "FAB-TWL-NVY"]},
    {"code": "WV-03", "name": "Air-jet loom 3 (wide)","stage": "weaving",  "floor_x": 4, "floor_y": 5, "fabric_codes": ["FAB-POP-BLU", "FAB-POP-GRY", "FAB-SHT-WHT", "FAB-TWL-NVY"]},
    {"code": "DY-01", "name": "Jigger 1",            "stage": "dyeing",    "floor_x": 7, "floor_y": 2, "fabric_codes": []},
    {"code": "DY-02", "name": "Jigger 2",            "stage": "dyeing",    "floor_x": 7, "floor_y": 4, "fabric_codes": []},
    {"code": "FN-01", "name": "Stenter",             "stage": "finishing", "floor_x": 9, "floor_y": 3, "fabric_codes": []},
]

# SEED §4 — buyers (default_late_penalty_paise_per_day)
DEMO_BUYERS = [
    {"code": "BUY-001", "name": "Kaveri Garments",       "payment_terms_days": 30, "default_late_penalty_paise_per_day": 300000},
    {"code": "BUY-002", "name": "Deccan Linens",         "payment_terms_days": 45, "default_late_penalty_paise_per_day": 500000},
    {"code": "BUY-003", "name": "Coastal Exports",       "payment_terms_days": 30, "default_late_penalty_paise_per_day": 400000},
    {"code": "BUY-004", "name": "Nilgiri Home Textiles", "payment_terms_days": 60, "default_late_penalty_paise_per_day": 200000},
]


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def seed_base(session: Session) -> None:
    """Seed fundamental data: mill_settings, shifts, defect codes, demo staff users."""
    _seed_mill_settings(session)
    _seed_shifts(session)
    _seed_defect_codes(session)
    _seed_users(session)


def seed_master_data(session: Session) -> None:
    """Seed all SEED §2-6 master data (idempotent)."""
    _seed_workers_and_users(session)
    _seed_suppliers_and_yarn_types(session)
    _seed_routes(session)
    _seed_fabric_types(session)
    _seed_machines(session)
    _seed_buyers(session)
    # Ensure mill_settings has production metrics
    from sqlalchemy import text
    session.execute(text("""
        UPDATE mill_settings SET
            qc_packing_paise_per_roll = :qc_pack,
            overhead_paise_per_m = :overhead,
            rework_cost_paise_per_m = :rework,
            machine_rate_paise_per_hour = :machine_rate,
            waste_norm_bp = :waste_norm
        WHERE qc_packing_paise_per_roll = 0
    """), {
        "qc_pack": DEMO_MILL["qc_packing_paise_per_roll"],
        "overhead": DEMO_MILL["overhead_paise_per_m"],
        "rework": DEMO_MILL["rework_cost_paise_per_m"],
        "machine_rate": json.dumps(DEMO_MILL["machine_rate_paise_per_hour"]),
        "waste_norm": json.dumps(DEMO_MILL["waste_norm_bp"]),
    })


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _seed_mill_settings(session: Session) -> None:
    from sqlalchemy import text
    exists = session.execute(text("SELECT COUNT(*) FROM mill_settings")).scalar()
    if not exists:
        session.execute(text("""
            INSERT INTO mill_settings (
                mill_name, timezone, gst_default_bp, overtime_multiplier_bp,
                order_tolerance_bp, aged_stock_days, health_amber_minutes,
                ripple_slip_threshold_minutes, qc_buffer_minutes, dispatch_buffer_minutes,
                rework_cost_paise_per_m, rework_minutes_per_roll,
                qc_packing_paise_per_roll, overhead_paise_per_m, state_version,
                machine_rate_paise_per_hour, waste_norm_bp, created_at
            ) VALUES (
                :mill_name, :tz, :gst, :ot_mult, :tol, :aged, :health_amber,
                :ripple_slip, :qc_buf, :dsp_buf,
                :rework, 0, :qc_pack, :overhead, 0,
                :machine_rate, :waste_norm, :now
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
            "rework": DEMO_MILL["rework_cost_paise_per_m"],
            "qc_pack": DEMO_MILL["qc_packing_paise_per_roll"],
            "overhead": DEMO_MILL["overhead_paise_per_m"],
            "machine_rate": json.dumps(DEMO_MILL["machine_rate_paise_per_hour"]),
            "waste_norm": json.dumps(DEMO_MILL["waste_norm_bp"]),
            "now": now(),
        })


def _seed_shifts(session: Session) -> None:
    from sqlalchemy import text
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


def _seed_defect_codes(session: Session) -> None:
    from sqlalchemy import text
    for d in DEMO_DEFECT_CODES:
        session.execute(text("""
            INSERT INTO defect_codes (id, code, label_en, default_severity, created_at)
            VALUES (gen_random_uuid(), :code, :label, :sev, :now)
            ON CONFLICT (code) DO NOTHING
        """), {"code": d["code"], "label": d["label_en"], "sev": d["default_severity"], "now": now()})


def _seed_users(session: Session) -> None:
    from sqlalchemy import text
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


def _seed_workers_and_users(session: Session) -> None:
    from sqlalchemy import text
    for w in DEMO_WORKERS:
        existing_w = session.execute(
            text("SELECT id FROM workers WHERE code = :code"), {"code": w["code"]}
        ).fetchone()
        worker_id = str(existing_w[0]) if existing_w else None
        if not existing_w:
            worker_id = str(uuid.uuid4())
            session.execute(text("""
                INSERT INTO workers (id, code, name, skill_stages, wage_type, wage_rate_paise,
                    piece_rate_paise_per_m, default_shift, overtime_willing,
                    preferred_language, is_active, created_at)
                VALUES (:id, :code, :name, :stages, :wt, :wr, :pr, :ds, :ot, :lang, true, :now)
            """), {
                "id": worker_id,
                "code": w["code"],
                "name": w["name"],
                "stages": w["skill_stages"],
                "wt": w["wage_type"],
                "wr": w["wage_rate_paise"],
                "pr": w.get("piece_rate_paise_per_m"),
                "ds": w["default_shift"],
                "ot": w["overtime_willing"],
                "lang": w["preferred_language"],
                "now": now(),
            })
        # Create operator user account (PIN 1234)
        existing_u = session.execute(
            text("SELECT id FROM users WHERE employee_code = :code"), {"code": w["code"]}
        ).fetchone()
        if not existing_u:
            session.execute(text("""
                INSERT INTO users (id, employee_code, name, role, pin_hash,
                    worker_id, preferred_language, is_active, created_at)
                VALUES (:id, :code, :name, 'operator', :pin, :wid, :lang, true, :now)
            """), {
                "id": str(uuid.uuid4()),
                "code": w["code"],
                "name": w["name"],
                "pin": hash_pin("1234"),
                "wid": worker_id,
                "lang": w["preferred_language"],
                "now": now(),
            })
    # Update EMP sequence
    from sqlalchemy import text as txt
    session.execute(txt("""
        INSERT INTO code_sequences (prefix, last_value) VALUES ('EMP', 12)
        ON CONFLICT (prefix) DO UPDATE SET last_value = GREATEST(code_sequences.last_value, 12)
    """))


def _seed_suppliers_and_yarn_types(session: Session) -> None:
    from sqlalchemy import text

    # Yarn types first (suppliers reference them)
    yt_id_map: dict[str, str] = {}
    for yt in DEMO_YARN_TYPES:
        existing = session.execute(
            text("SELECT id FROM yarn_types WHERE code = :code"), {"code": yt["code"]}
        ).fetchone()
        if existing:
            yt_id_map[yt["code"]] = str(existing[0])
        else:
            yt_id = str(uuid.uuid4())
            yt_id_map[yt["code"]] = yt_id
            session.execute(text("""
                INSERT INTO yarn_types (id, code, material, count_label, colour, colour_hex,
                    reorder_level_g, standard_rate_paise_per_kg, is_active, created_at)
                VALUES (:id, :code, :mat, :cnt, :col, :hex, :rl, :rate, true, :now)
            """), {
                "id": yt_id, "code": yt["code"], "mat": yt["material"],
                "cnt": yt["count_label"], "col": yt["colour"],
                "hex": yt.get("colour_hex"),
                "rl": yt["reorder_level_g"],
                "rate": yt["standard_rate_paise_per_kg"],
                "now": now(),
            })

    # Suppliers + supplier_yarn_types
    for sup in DEMO_SUPPLIERS:
        existing = session.execute(
            text("SELECT id FROM suppliers WHERE code = :code"), {"code": sup["code"]}
        ).fetchone()
        if existing:
            continue
        sup_id = str(uuid.uuid4())
        session.execute(text("""
            INSERT INTO suppliers (id, code, name, payment_terms_days, is_active, created_at)
            VALUES (:id, :code, :name, :pt, true, :now)
        """), {
            "id": sup_id, "code": sup["code"],
            "name": sup["name"], "pt": sup["payment_terms_days"],
            "now": now(),
        })
        for ycode in sup["yarn_codes"]:
            yt_id = yt_id_map.get(ycode)
            if yt_id:
                session.execute(text("""
                    INSERT INTO supplier_yarn_types (id, supplier_id, yarn_type_id, created_at)
                    VALUES (gen_random_uuid(), :sid, :ytid, :now)
                    ON CONFLICT DO NOTHING
                """), {"sid": sup_id, "ytid": yt_id, "now": now()})

    # Advance SUP sequence
    session.execute(text("""
        INSERT INTO code_sequences (prefix, last_value) VALUES ('SUP', 3)
        ON CONFLICT (prefix) DO UPDATE SET last_value = GREATEST(code_sequences.last_value, 3)
    """))


def _seed_routes(session: Session) -> None:
    from sqlalchemy import text
    for r in DEMO_ROUTES:
        existing = session.execute(
            text("SELECT id FROM route_templates WHERE name = :name"), {"name": r["name"]}
        ).fetchone()
        if existing:
            continue
        rid = str(uuid.uuid4())
        session.execute(text("""
            INSERT INTO route_templates (id, name, description, created_at)
            VALUES (:id, :name, :desc, :now)
        """), {"id": rid, "name": r["name"], "desc": r.get("description"), "now": now()})
        for step in r["steps"]:
            session.execute(text("""
                INSERT INTO route_steps (id, template_id, seq, stage, buffer_minutes, created_at)
                VALUES (gen_random_uuid(), :tid, :seq, :stage, :buf, :now)
            """), {
                "tid": rid, "seq": step["seq"],
                "stage": step["stage"], "buf": step["buffer_minutes"],
                "now": now(),
            })


def _seed_fabric_types(session: Session) -> None:
    from sqlalchemy import text
    for ft in DEMO_FABRIC_TYPES:
        existing = session.execute(
            text("SELECT id FROM fabric_types WHERE code = :code"), {"code": ft["code"]}
        ).fetchone()
        if existing:
            continue
        yt_row = session.execute(
            text("SELECT id FROM yarn_types WHERE code = :code"), {"code": ft["yarn_code"]}
        ).fetchone()
        rt_row = session.execute(
            text("SELECT id FROM route_templates WHERE name = :name"), {"name": ft["route_name"]}
        ).fetchone()
        if not yt_row or not rt_row:
            continue
        session.execute(text("""
            INSERT INTO fabric_types (id, code, name, width_cm, gsm, colour,
                yarn_type_id, yarn_g_per_100m, route_template_id, hsn_code,
                default_price_paise_per_m, gst_bp, is_active, created_at)
            VALUES (gen_random_uuid(), :code, :name, :w, :gsm, :col,
                :yt, :yarn_g, :rt, :hsn, :price, 500, true, :now)
        """), {
            "code": ft["code"], "name": ft["name"],
            "w": ft["width_cm"], "gsm": ft.get("gsm"),
            "col": ft["colour"],
            "yt": str(yt_row[0]), "yarn_g": ft["yarn_g_per_100m"],
            "rt": str(rt_row[0]), "hsn": ft.get("hsn_code", "5208"),
            "price": ft["default_price_paise_per_m"],
            "now": now(),
        })


def _seed_machines(session: Session) -> None:
    from sqlalchemy import text
    for m in DEMO_MACHINES:
        existing = session.execute(
            text("SELECT id FROM machines WHERE code = :code"), {"code": m["code"]}
        ).fetchone()
        if existing:
            continue
        mid = str(uuid.uuid4())
        session.execute(text("""
            INSERT INTO machines (id, code, name, stage, floor_x, floor_y, status, unit, idle_cost_paise_per_hour, created_at)
            VALUES (:id, :code, :name, :stage, :fx, :fy, 'idle', 'cm', 0, :now)
        """), {
            "id": mid, "code": m["code"], "name": m.get("name", m["code"]),
            "stage": m["stage"], "fx": m["floor_x"], "fy": m["floor_y"], "now": now(),
        })
        for fc in m["fabric_codes"]:
            ft_row = session.execute(
                text("SELECT id FROM fabric_types WHERE code = :code"), {"code": fc}
            ).fetchone()
            if ft_row:
                session.execute(text("""
                    INSERT INTO machine_capabilities (id, machine_id, fabric_type_id, created_at)
                    VALUES (gen_random_uuid(), :mid, :fid, :now)
                    ON CONFLICT DO NOTHING
                """), {"mid": mid, "fid": str(ft_row[0]), "now": now()})


def _seed_buyers(session: Session) -> None:
    from sqlalchemy import text
    for b in DEMO_BUYERS:
        existing = session.execute(
            text("SELECT id FROM buyers WHERE code = :code"), {"code": b["code"]}
        ).fetchone()
        if not existing:
            session.execute(text("""
                INSERT INTO buyers (id, code, name, payment_terms_days,
                    default_late_penalty_paise_per_day, is_active, created_at)
                VALUES (gen_random_uuid(), :code, :name, :pt, :penalty, true, :now)
            """), {
                "code": b["code"], "name": b["name"],
                "pt": b["payment_terms_days"],
                "penalty": b["default_late_penalty_paise_per_day"],
                "now": now(),
            })
    # Advance BUY sequence
    session.execute(text("""
        INSERT INTO code_sequences (prefix, last_value) VALUES ('BUY', 4)
        ON CONFLICT (prefix) DO UPDATE SET last_value = GREATEST(code_sequences.last_value, 4)
    """))
