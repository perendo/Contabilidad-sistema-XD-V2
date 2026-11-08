import re

from pydantic import BaseModel, ConfigDict, Field

ACCOUNT_TYPES = {"Activo", "Pasivo", "Patrimonio Neto", "Ingreso", "Gasto"}


def _escape_like(value: str) -> str:
    return re.sub(r"([%_])", r"\\\1", value)


class AccountIn(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    type: str
    level: int = Field(ge=1, le=8)
    is_detail: bool = False
    parent_id: int | None = None


class AccountOut(AccountIn):
    id: int
    model_config = ConfigDict(from_attributes=True)
