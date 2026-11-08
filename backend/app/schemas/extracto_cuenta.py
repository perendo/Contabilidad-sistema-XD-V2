from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class MovementOut(BaseModel):
    date: date
    entry_id: int
    entry_description: str
    description: str
    debit: Decimal | float | None
    credit: Decimal | float | None
    running_balance: Decimal | float | None

    @field_serializer("debit", "credit", "running_balance")
    def _serialize_amount(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"


class ExtractoCuentaOut(BaseModel):
    account_id: int
    account_code: str
    account_name: str
    date_from: date | None
    date_to: date | None
    initial_balance: Decimal | float | None
    movements: list[MovementOut]
    total_debit: Decimal | float | None
    total_credit: Decimal | float | None
    final_balance: Decimal | float | None
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("initial_balance", "total_debit", "total_credit", "final_balance")
    def _serialize_total(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"
