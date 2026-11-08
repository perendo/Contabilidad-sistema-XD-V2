from datetime import date

from pydantic import BaseModel, ConfigDict


class Modelo111Summary(BaseModel):
    base: float
    retenciones_a_ingresar: float


class PagosACuenta130Summary(BaseModel):
    base: float
    retenciones_soportadas: float


class IRPFSummaryOut(BaseModel):
    year: int
    quarter: int
    modelo_111: Modelo111Summary
    pagos_a_cuenta_130: PagosACuenta130Summary
    facturas_emitidas_count: int
    facturas_recibidas_count: int
    model_config = ConfigDict(from_attributes=True)
