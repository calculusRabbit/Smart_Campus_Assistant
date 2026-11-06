import re
from datetime import date
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,  # restricts password display
    StringConstraints,
    field_validator,
    model_validator,
)

from models import Interest


def normalize_email(value: str) -> str:
    value = value.lower()

    if re.fullmatch(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z0-9\-]{2,}$", value) is None:
        raise ValueError(
            "email contains unsupported characters. "
            "Allowed characters: letters, digits, ., _, %, +, -."
        )
    return value


type AccountEmail = Annotated[EmailStr, AfterValidator(normalize_email)]


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # reject extra JSON fiellds

    username: str = Field(
        min_length=5,
        max_length=30,
        pattern=r"^[A-Za-z0-9_,@!\-]+$",
    )
    first_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)
    ]
    last_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    email: AccountEmail
    dob: date
    zipcode: str | None = Field(default=None, pattern=r"^[0-9]{5}(-[0-9]{4})?$")
    latitude_approx: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude_approx: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    is_primary: bool
    degree_level: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    majors: list[
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    ] = Field(default_factory=list, max_length=20)
    minors: list[
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    ] = Field(default_factory=list, max_length=20)
    password: SecretStr = Field(min_length=8, max_length=128)
    interests: list[Interest] = Field(default_factory=list, max_length=50)
    scorecard_id: int = Field(gt=0)
    program: str = Field(default="", max_length=100)
    captcha: str = Field(max_length=8192)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if any(word in value.casefold() for word in ("admin", "system", "alert")):
            raise ValueError("Username contains a reserved phrase")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        password = value.get_secret_value()
        special = " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        if not all(
            (
                any("A" <= c <= "Z" for c in password),
                any("a" <= c <= "z" for c in password),
                any("0" <= c <= "9" for c in password),
                any(c in special for c in password),
            )
        ):
            raise ValueError("Password requires uppercase, lowercase, digit and special character")
        return value

    @model_validator(mode="after")
    def validate_location(self) -> Self:
        lat = self.latitude_approx
        lon = self.longitude_approx

        if (lat is None) != (lon is None):
            raise ValueError("Provide both coordinates")

        if self.zipcode is None and lat is None:
            raise ValueError("Provide a zipcode or browser location")

        if lat is not None and lon is not None:
            self.latitude_approx = round(lat, 2)
            self.longitude_approx = round(lon, 2)

        return self

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, value: date) -> date:

        today = date.today()
        age = today.year - value.year
        if (today.month, today.day) < (value.month, value.day):
            age -= 1

        if value < date(1940, 1, 1) or age < 14:
            raise ValueError("DOB must be after 1939 and you must be at least 14")

        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: AccountEmail
    password: SecretStr = Field(min_length=8, max_length=128)


class ReauthenticateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: SecretStr = Field(min_length=8, max_length=128)


class DeactivateRequest(ReauthenticateRequest):
    captcha: str = Field(max_length=8192)
