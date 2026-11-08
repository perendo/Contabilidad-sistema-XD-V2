from pydantic import BaseModel, ConfigDict


class ThirdPartySummaryOut(BaseModel):
    third_party_id: int
    tax_id: str
    name: str
    total_annual: float


class Modelo347Out(BaseModel):
    year: int
    threshold: float
    third_parties: list[ThirdPartySummaryOut]
    model_config = ConfigDict(from_attributes=True)
