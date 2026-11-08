from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer

VAT_RATES = [Decimal("21"), Decimal("10"), Decimal("4"), Decimal("0")]


class IVARateBreakdown(BaseModel):
    devengado: Decimal | float | None
    deducible: Decimal | float | None

    @field_serializer("devengado", "deducible")
    def _serialize_amount(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"


class IVALiquidationOut(BaseModel):
    date_from: date | None
    date_to: date | None
    iva_devengado: Decimal | float | None
    iva_deducible: Decimal | float | None
    saldo: Decimal | float | None
    tipo_saldo: str
    breakdown: dict[str, IVARateBreakdown]
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("iva_devengado", "iva_deducible", "saldo")
    def _serialize_total(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"
