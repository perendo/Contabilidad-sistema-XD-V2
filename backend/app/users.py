import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import User

router = APIRouter(prefix="/users", tags=["users"])


class UserIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=list[UserOut])
def list_users(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[User]:
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserIn,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    user = User(
        email=body.email,
        password_hash=bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode(),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado"
        )
    db.refresh(user)
    return user
