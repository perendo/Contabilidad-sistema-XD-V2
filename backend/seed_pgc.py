import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
from app.database import SessionLocal
from app.pgc_seed import seed_pgc

if __name__ == "__main__":
    db = SessionLocal()
    try:
        n = seed_pgc(db)
        print(f"Seeded {n} accounts from PGC.")
    finally:
        db.close()
