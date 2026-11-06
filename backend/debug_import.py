import sys
sys.path.insert(0, ".")
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import User, Company
import bcrypt

eng = create_engine(settings.test_database_url, pool_pre_ping=True)
Base.metadata.drop_all(bind=eng)
Base.metadata.create_all(bind=eng)
db = sessionmaker(bind=eng)()
if not db.query(User).filter(User.email == "test@example.com").first():
    db.add(User(email="test@example.com", password_hash=bcrypt.hashpw(b"testpass123", bcrypt.gensalt()).decode()))
if not db.query(Company).first():
    db.add(Company(name="E", tax_id="B0", address="", fiscal_year="2026"))
db.commit()
db.close()

def override():
    s = sessionmaker(bind=eng)()
    try:
        yield s
    finally:
        s.close()

app.dependency_overrides[get_db] = override
c = TestClient(app)
login = c.post("/auth/login", json={"email": "test@example.com", "password": "testpass123"})
h = {"Authorization": f"Bearer {login.json()['access_token']}"}
exp = c.post("/accounts", json={"code": "6000", "name": "Gasto test", "type": "Gasto", "level": 1, "is_detail": True}, headers=h).json()
c.post("/accounts", json={"code": "4720", "name": "IVA", "type": "Activo", "level": 1, "is_detail": True}, headers=h)

# read the xml sample from test file
import re
src = open("tests/test_received_invoices.py").read()
start = src.index('FACTURAE_SAMPLE = """')
end = src.index('"""', start + len('FACTURAE_SAMPLE = """'))
xml = src[start + len('FACTURAE_SAMPLE = """'):end]

resp = c.post("/received-invoices/import", files={"file": ("factura.xml", xml.encode("utf-8"), "application/xml")}, data={"expense_account_id": str(exp["id"])}, headers=h)
print("STATUS:", resp.status_code)
print("BODY:", resp.text)
"