from datetime import date as DateType
from decimal import Decimal, ROUND_HALF_UP

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

ALLOWED_VAT_RATES = {Decimal("21"), Decimal("10"), Decimal("4"), Decimal("0")}
CENT = Decimal("0.01")


class InvoiceIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    date: DateType = Field(validation_alias=AliasChoices("date", "fecha"))
    third_party_id: int = Field(
        validation_alias=AliasChoices(
            "third_party_id", "client_id", "cliente_id", "tercero_id"
        )
    )
    description: str = Field(
        default="",
        max_length=500,
        validation_alias=AliasChoices("description", "concept", "concepto"),
    )
    base_amount: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        validation_alias=AliasChoices("base_amount", "base", "base_imponible"),
    )
    vat_rate: Decimal = Field(
        validation_alias=AliasChoices("vat_rate", "iva", "tipo_iva")
    )
    irpf_rate: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "irpf_rate", "retencion_irpf", "tipo_retencion"
        ),
    )
    irpf_amount: Decimal | None = Field(
        default=None,
        validation_alias=AliasChoices("irpf_amount", "importe_retencion"),
    )


class InvoiceOut(BaseModel):
    id: int
    year: int
    number: int
    date: DateType
    third_party_id: int
    description: str
    base_amount: float
    vat_rate: float
    vat_amount: float
    total: float
    irpf_rate: float | None
    irpf_amount: float | None
    entry_id: int | None
    status: str
    model_config = ConfigDict(from_attributes=True)


class InvoicePayIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    status: str = Field(validation_alias=AliasChoices("status", "estado"))
