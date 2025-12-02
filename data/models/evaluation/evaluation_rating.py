from pydantic import BaseModel

class EvaluationRating(BaseModel):
    """
    Data model for evaluation rating results with rating and rationale.
    """
    rating: str
    rationale: str