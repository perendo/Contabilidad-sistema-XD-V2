from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class ThirdPartySummaryOut(BaseModel):
    third_party_id: int
    tax_id: str
    name: str
    total_annual: Decimal | float | None

    @field_serializer("total_annual")
    def _serialize_amount(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"


class Modelo347Out(BaseModel):
    year: int
    threshold: Decimal | float | None
    third_parties: list[ThirdPartySummaryOut]
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("threshold")
    def _serialize_threshold(self, v: Decimal | float | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"
