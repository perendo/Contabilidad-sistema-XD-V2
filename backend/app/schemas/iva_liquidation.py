from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

VAT_RATES = [Decimal("21"), Decimal("10"), Decimal("4"), Decimal("0")]


class IVARateBreakdown(BaseModel):
    devengado: float
    deducible: float


class IVALiquidationOut(BaseModel):
    date_from: date | None
    date_to: date | None
    iva_devengado: float
    iva_deducible: float
    saldo: float
    tipo_saldo: str
    breakdown: dict[str, IVARateBreakdown]
    model_config = ConfigDict(from_attributes=True)
