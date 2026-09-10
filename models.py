from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class RecommendationRequest(BaseModel):
    interests: list[str]


class StudentInterestsRequest(BaseModel):
    interests: list[str]