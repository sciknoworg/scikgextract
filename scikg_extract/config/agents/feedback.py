"""
FeedbackConfig dataclass for configuring the feedback generation step.

Specifies the LLM used to generate updated prompts incorporating judge feedback, as well as any formatting or prompt-template overrides for the feedback agent.
"""
# Python imports
from dataclasses import dataclass

@dataclass
class FeedbackConfig:
    """
    Configuration dataclass for the Feedback Agent to be used in providing feedback on extracted structured processes.
    """
    
    # Name of the LLM model to be used for feedback generation
    llm_name: str
