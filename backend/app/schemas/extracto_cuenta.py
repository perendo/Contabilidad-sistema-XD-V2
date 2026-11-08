from datetime import date

from pydantic import BaseModel, ConfigDict


class MovementOut(BaseModel):
    date: date
    entry_id: int
    entry_description: str
    description: str
    debit: float
    credit: float
    running_balance: float


class ExtractoCuentaOut(BaseModel):
    account_id: int
    account_code: str
    account_name: str
    date_from: date | None
    date_to: date | None
    movements: list[MovementOut]
    total_debit: float
    total_credit: float
    final_balance: float
    model_config = ConfigDict(from_attributes=True)
