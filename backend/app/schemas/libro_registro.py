from datetime import date

from pydantic import BaseModel, ConfigDict


class RegistroFacturaOut(BaseModel):
    date: date
    number: int | None
    supplier_number: str | None
    third_party_id: int
    third_party_tax_id: str
    third_party_name: str
    description: str
    base_amount: float
    vat_rate: float
    vat_amount: float
    irpf_rate: float | None
    irpf_amount: float | None
    total: float


class LibroRegistroOut(BaseModel):
    year: int
    emitidas: list[RegistroFacturaOut]
    recibidas: list[RegistroFacturaOut]
    total_emitidas: float
    total_recibidas: float
    model_config = ConfigDict(from_attributes=True)
