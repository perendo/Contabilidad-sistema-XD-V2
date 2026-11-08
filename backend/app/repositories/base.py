"""Capa de repositorios: acceso a datos centralizado.

Cada repositorio recibe una sesion de SQLAlchemy y expone metodos de
lectura/escritura sobre una tabla. No contiene logica de negocio.
"""
from typing import TypeVar

from sqlalchemy.orm import Session

from ..database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository:
    def __init__(self, db: Session, model: type[ModelType]) -> None:
        self.db = db
        self.model = model

    def get(self, id: int) -> ModelType | None:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def list(self, *, offset: int = 0, limit: int = 100):
        return self.db.query(self.model).offset(offset).limit(limit).all()

    def add(self, instance: ModelType) -> ModelType:
        self.db.add(instance)
        self.db.flush()
        return instance

    def delete(self, instance: ModelType) -> None:
        self.db.delete(instance)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, instance: ModelType) -> None:
        self.db.refresh(instance)
