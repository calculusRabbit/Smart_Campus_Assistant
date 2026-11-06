from datetime import date
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,  #restricts password display
    StringConstraints,
    field_validator,
)

from models import Interest


class SignupRequest(BaseModel):

    model_config = ConfigDict(extra="forbid") #reject extra JSON fiellds

    username: str = Field(
        min_length=5,
        max_length=30,
        pattern = r"^[A-Za-z0-9_!]+$",
    )
    first_name: Annotated[str,StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
    last_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    email: EmailStr
    dob: date
    zipcode: str = Field(pattern = r"^[0-9]{5}(-[0-9]{4})?$")
    password: SecretStr = Field(min_length=8, max_length=128)
    interests: list[Interest] = Field(default_factory=list, max_length=50)
    scorecard_id: int = Field(gt=0)
    program: str = Field(default="", max_length=100)
    captcha: str = Field(max_length=8192)

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

    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)


class ReauthenticateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: SecretStr = Field(min_length=8, max_length=128)


class DeactivateRequest(ReauthenticateRequest):
    captcha: str = Field(max_length=8192)