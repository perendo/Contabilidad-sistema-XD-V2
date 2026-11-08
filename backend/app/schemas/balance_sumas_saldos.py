from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class BalanceAccountOut(BaseModel):
    code: str
    name: str
    debe: Decimal | float | None
    haber: Decimal | float | None
    saldo: Decimal | float | None

    @field_serializer("debe", "haber", "saldo")
    def _serialize_amount(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"


class BalanceSumasSaldosOut(BaseModel):
    date_from: date | None
    date_to: date | None
    accounts: list[BalanceAccountOut]
    total_debe: Decimal | float | None
    total_haber: Decimal | float | None
    cuadrado: bool
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("total_debe", "total_haber")
    def _serialize_total(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"
