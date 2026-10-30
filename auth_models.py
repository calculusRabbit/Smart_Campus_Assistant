from datetime import date
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr, #restricts password display
    StringConstraints,
    field_validator,
)


Interest = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=200,
    ),
]


class SignupRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        min_length=5,
        max_length=30,
        pattern = r"^[A-Za-z0-9_]+$",
    )
    first_name: str = Field(min_length=1, max_length=30)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    dob: date
    zipcode: str = Field(pattern = r"^[0-9]{5}(-[0-9]{4})?$")
    password: SecretStr = Field(min_length=8, max_length=128)
    interests: list[Interest] = Field(default_factory=list, max_length=50)

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, value: date) -> date:
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

        if value < date(1940, 1, 1) or age < 14:
            raise ValueError("DOB must be after 1940 and you must be at least 14")

        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)


class ReauthenticateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: SecretStr = Field(min_length=8, max_length=128)