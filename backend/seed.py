import bcrypt

from app.config import settings
from app.database import SessionLocal
from app.models import User


def main():
    if not settings.seed_email or not settings.seed_password:
        raise SystemExit("SEED_EMAIL and SEED_PASSWORD must be set in .env")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.seed_email).first()
        if existing:
            print(f"Seed user already exists: {settings.seed_email}")
            return
        hashed = bcrypt.hashpw(settings.seed_password.encode(), bcrypt.gensalt()).decode()
        user = User(email=settings.seed_email, password_hash=hashed)
        db.add(user)
        db.commit()
        print(f"Seed user created: {settings.seed_email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
