from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class CompanyIn(BaseModel):
    name: str
    tax_id: str
    address: str
    fiscal_year: str
    approval_threshold: Decimal | None = None


class CompanyOut(CompanyIn):
    id: int
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("approval_threshold")
    def _serialize_threshold(self, v: Decimal | None) -> str | None:
        if v is None:
            return None
        return f"{v:.2f}"
