"""Entry point: alembic upgrade head + seed base + optional scenario."""
from __future__ import annotations
import sys


def main() -> None:
    reset = "--reset" in sys.argv

    import subprocess
    if reset:
        # DROP CASCADE avoids FK-order issues that alembic downgrade can't handle
        from app.db import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
    subprocess.check_call(["alembic", "upgrade", "head"])

    from app.db import SessionLocal
    from app.seed.base import seed_base, seed_master_data
    from app.seed.history import run as seed_history

    with SessionLocal() as session:
        seed_base(session)
        session.commit()
        seed_master_data(session)
        session.commit()
        seed_history(session)
        session.commit()
        print("Base + master data + history seed complete.")

    if "--scenario" in sys.argv or reset:
        from app.seed import scenario_demo
        with SessionLocal() as session:
            scenario_demo.run(session)
            session.commit()
        print("Demo scenario applied.")


if __name__ == "__main__":
    main()
