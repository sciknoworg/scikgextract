# Python imports
from dataclasses import dataclass

@dataclass
class FeedbackConfig:
    """
    Configuration dataclass for the Feedback Agent to be used in providing feedback on extracted structured processes.
    """
    
    # Name of the LLM model to be used for feedback generation
    llm_name: str
