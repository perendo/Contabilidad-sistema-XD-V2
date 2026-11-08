from datetime import date as DateType
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, AliasChoices

ALLOWED_STATUSES = {"draft", "accepted"}


class JournalLineIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    account_id: int = Field(
        validation_alias=AliasChoices("account_id", "accountId", "cuenta_id")
    )
    description: str = Field(
        default="",
        validation_alias=AliasChoices("description", "concept", "concepto"),
    )
    debit: Decimal = Field(
        default=Decimal("0"),
        validation_alias=AliasChoices("debit", "debe"),
    )
    credit: Decimal = Field(
        default=Decimal("0"),
        validation_alias=AliasChoices("credit", "haber"),
    )


class JournalEntryIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    date: DateType = Field(validation_alias=AliasChoices("date", "fecha"))
    description: str = Field(
        default="",
        validation_alias=AliasChoices("description", "concept", "concepto"),
    )
    status: str | None = Field(
        default=None,
        validation_alias=AliasChoices("status", "estado"),
    )
    lines: list[JournalLineIn] = Field(
        validation_alias=AliasChoices("lines", "lineas", "apuntes")
    )


class JournalLineOut(BaseModel):
    id: int
    account_id: int
    description: str
    debit: Decimal
    credit: Decimal
    model_config = ConfigDict(
        from_attributes=True, json_encoders={Decimal: lambda v: f"{v:.2f}"}
    )


class JournalEntryOut(BaseModel):
    id: int
    date: DateType
    description: str
    status: str
    reviewed: bool
    author: str | None = None
    correction_of_entry_id: int | None = None
    corrects_entry_id: int | None = None
    original_entry_id: int | None = None
    lines: list[JournalLineOut]
    model_config = ConfigDict(from_attributes=True)
