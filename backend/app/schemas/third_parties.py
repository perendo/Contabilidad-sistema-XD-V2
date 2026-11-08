from pydantic import BaseModel, ConfigDict, Field, AliasChoices

ALLOWED_TYPES = {"cliente", "proveedor", "Cliente", "Proveedor"}


def _normalize_type(value: str) -> str:
    low = value.strip().lower()
    if low in ("cliente",):
        return "Cliente"
    if low in ("proveedor",):
        return "Proveedor"
    raise ValueError("Tipo de tercero no válido")


class ThirdPartyIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(
        min_length=1, max_length=255,
        validation_alias=AliasChoices("name", "nombre", "razon_social"),
    )
    tax_id: str = Field(
        min_length=1, max_length=50,
        validation_alias=AliasChoices("tax_id", "nif", "cif", "nif_cif"),
    )
    type: str = Field(validation_alias=AliasChoices("type", "tipo"))
    account_id: int = Field(
        validation_alias=AliasChoices(
            "account_id", "accountId", "cuenta_id", "subcuenta_id"
        )
    )
    address: str = Field(
        default="", max_length=500,
        validation_alias=AliasChoices("address", "domicilio", "direccion"),
    )
    phone: str = Field(
        default="", max_length=50,
        validation_alias=AliasChoices("phone", "telefono"),
    )
    email: str = Field(
        default="", max_length=255,
        validation_alias=AliasChoices("email", "correo"),
    )


class ThirdPartyOut(ThirdPartyIn):
    id: int
    type: str
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
