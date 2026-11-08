from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class RegistroFacturaOut(BaseModel):
    date: date
    number: int | None
    supplier_number: str | None
    third_party_id: int
    third_party_tax_id: str
    third_party_name: str
    description: str
    base_amount: Decimal | float | None
    vat_rate: Decimal | float | None
    vat_amount: Decimal | float | None
    irpf_rate: Decimal | float | None
    irpf_amount: Decimal | float | None
    total: Decimal | float | None

    @field_serializer(
        "base_amount",
        "vat_rate",
        "vat_amount",
        "irpf_rate",
        "irpf_amount",
        "total",
    )
    def _serialize_amount(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"


class LibroRegistroOut(BaseModel):
    year: int
    emitidas: list[RegistroFacturaOut]
    recibidas: list[RegistroFacturaOut]
    total_emitidas: Decimal | float | None
    total_recibidas: Decimal | float | None
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("total_emitidas", "total_recibidas")
    def _serialize_total(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"
