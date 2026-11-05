import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import User

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_user():
    db = TestingSessionLocal()
    try:
        if not db.query(User).filter(User.email == TEST_EMAIL).first():
            hashed = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt()).decode()
            db.add(User(email=TEST_EMAIL, password_hash=hashed))
            db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "documents_dir", tmp_path / "Data")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _seed_user()
    yield


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
