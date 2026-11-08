from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class Modelo111Summary(BaseModel):
    base: Decimal | float | None
    retenciones_a_ingresar: Decimal | float | None

    @field_serializer("base", "retenciones_a_ingresar")
    def _serialize_amount(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"


class PagosACuenta130Summary(BaseModel):
    base: Decimal | float | None
    retenciones_soportadas: Decimal | float | None

    @field_serializer("base", "retenciones_soportadas")
    def _serialize_amount(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"


class IRPFSummaryOut(BaseModel):
    year: int
    quarter: int
    modelo_111: Modelo111Summary
    pagos_a_cuenta_130: PagosACuenta130Summary
    facturas_emitidas_count: int
    facturas_recibidas_count: int
    model_config = ConfigDict(from_attributes=True)
