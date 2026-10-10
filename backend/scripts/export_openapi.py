"""Export OpenAPI JSON schema to docs/openapi.json."""
import json
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import create_app

app = create_app()
schema = app.openapi()

out = Path(__file__).parent.parent.parent / "docs" / "openapi.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(schema, indent=2, ensure_ascii=False))
print(f"OpenAPI schema written to {out}")