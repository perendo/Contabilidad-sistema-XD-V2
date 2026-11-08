from datetime import date

from pydantic import BaseModel, ConfigDict


class CuentaPerdidasGananciasOut(BaseModel):
    date_from: date | None
    date_to: date | None
    total_ingresos: float
    total_gastos: float
    resultado: float
    tipo_resultado: str
    model_config = ConfigDict(from_attributes=True)
