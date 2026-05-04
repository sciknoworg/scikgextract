from pydantic import BaseModel

class CriticResponse(BaseModel):
    """
    Data model for the critic's response in the debate-based evaluation. The critic reviews an evaluator's assessment and returns whether they are satisfied, a detailed critique, and an optional suggested rating.
    """
    satisfied: bool
    critique: str
    suggested_rating: str | None = None
