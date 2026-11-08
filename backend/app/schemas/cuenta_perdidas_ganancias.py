from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class CuentaPerdidasGananciasOut(BaseModel):
    date_from: date | None
    date_to: date | None
    total_ingresos: Decimal | float | None
    total_gastos: Decimal | float | None
    resultado: Decimal | float | None
    tipo_resultado: str
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("total_ingresos", "total_gastos", "resultado")
    def _serialize_amount(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"
