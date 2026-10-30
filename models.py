from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


Interest = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=200,
    ),
]


class ChatRequest(BaseModel):
    message: str = Field(max_length=4000)


class RecommendationRequest(BaseModel):
    interests: list[Interest] = Field(max_length=50)


class StudentInterestsRequest(BaseModel):
    interests: list[Interest] = Field(max_length=50)