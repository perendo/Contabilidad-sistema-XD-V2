from pydantic import BaseModel, ConfigDict, EmailStr


class UserIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    model_config = ConfigDict(from_attributes=True)
