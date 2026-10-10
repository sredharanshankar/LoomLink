"""Entry point: alembic upgrade head + seed base + optional scenario."""
from __future__ import annotations
import sys


def main() -> None:
    import subprocess
    subprocess.check_call(["alembic", "upgrade", "head"])

    from app.db import SessionLocal
    from app.seed.base import seed_base

    with SessionLocal() as session:
        seed_base(session)
        session.commit()
        print("Base seed complete.")

    if "--scenario" in sys.argv:
        from app.seed import scenario_demo
        with SessionLocal() as session:
            scenario_demo.run(session)
            session.commit()
        print("Demo scenario applied.")


if __name__ == "__main__":
    main()