from datetime import date

from pydantic import BaseModel, ConfigDict


class BalanceAccountOut(BaseModel):
    code: str
    name: str
    debe: float
    haber: float
    saldo: float


class BalanceSumasSaldosOut(BaseModel):
    date_from: date | None
    date_to: date | None
    accounts: list[BalanceAccountOut]
    total_debe: float
    total_haber: float
    cuadrado: bool
    model_config = ConfigDict(from_attributes=True)
