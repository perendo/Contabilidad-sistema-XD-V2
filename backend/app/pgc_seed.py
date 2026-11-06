import json
from pathlib import Path

from sqlalchemy.orm import Session

from .models import Account

PGC_PATH = Path(__file__).resolve().parents[1] / "data" / "pg_sample.json"

TYPE_MAP = {
    "activo": "Activo",
    "pasivo": "Pasivo",
    "patrimonio_neto": "Patrimonio Neto",
    "ingreso": "Ingreso",
    "gasto": "Gasto",
}


def seed_pgc(db: Session, company_id: int | None = None) -> int:
    """Seed the chart of accounts from pg_sample.json. Returns number inserted."""
    if not PGC_PATH.exists():
        return 0
    data = json.loads(PGC_PATH.read_text(encoding="utf-8"))
    q = db.query(Account)
    if company_id is not None:
        q = q.filter(Account.company_id == company_id)
    existing = {a.code: a for a in q.all()}
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
                pq = db.query(Account).filter(Account.code == parent_code)
                if company_id is not None:
                    pq = pq.filter(Account.company_id == company_id)
                parent = pq.first()
        account = Account(
            code=code,
            name=item["nombre"],
            type=TYPE_MAP.get(item["tipo"], item["tipo"]),
            level=item["nivel"],
            is_detail=bool(item.get("es_cuenta_registro", False)),
            parent_id=parent.id if parent else None,
            company_id=company_id,
        )
        db.add(account)
        db.flush()
        existing[code] = account
        inserted += 1
    db.commit()
    return inserted
