from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.ml.predictor import predict_event_categories

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


class EventPredictionRequest(BaseModel):
    title: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=5000)


@router.post("/predict-event")
def predict_event(request: EventPredictionRequest) -> dict:
    """Classify an event without changing existing recommendation behavior."""
    return predict_event_categories(request.title, request.description)
