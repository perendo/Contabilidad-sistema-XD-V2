import json
from pathlib import Path

from sqlalchemy.orm import Session

from .models import Account

PGC_PATH = Path(__file__).resolve().parents[2] / "Data" / "pg_sample.json"

TYPE_MAP = {
    "activo": "Activo",
    "pasivo": "Pasivo",
    "patrimonio_neto": "Patrimonio Neto",
    "ingreso": "Ingreso",
    "gasto": "Gasto",
}


def seed_pgc(db: Session) -> int:
    """Seed the chart of accounts from pg_sample.json. Returns number inserted."""
    if not PGC_PATH.exists():
        return 0
    data = json.loads(PGC_PATH.read_text(encoding="utf-8"))
    existing = {a.code: a for a in db.query(Account).all()}
    inserted = 0
    for item in sorted(data, key=lambda x: x["nivel"]):
        code = item["codigo"]
        if code in existing:
            continue
        parent = None
        parent_code = item.get("codigo_padre")
        if parent_code:
            parent = existing.get(parent_code)
            if parent is None:
                parent = db.query(Account).filter(Account.code == parent_code).first()
        account = Account(
            code=code,
            name=item["nombre"],
            type=TYPE_MAP.get(item["tipo"], item["tipo"]),
            level=item["nivel"],
            is_detail=bool(item.get("es_cuenta_registro", False)),
            parent_id=parent.id if parent else None,
        )
        db.add(account)
        db.flush()
        existing[code] = account
        inserted += 1
    db.commit()
    return inserted
