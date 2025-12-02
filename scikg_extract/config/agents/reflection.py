# Python imports
from dataclasses import dataclass

# External imports
from yescieval.base.rubric import Rubric

@dataclass
class ReflectionConfig:
    """
    Configuration dataclass for the Reflection Agent to be used in validating extracted structured knowledge using LLM-as-a-Judge paradigm.
    """
    # Name of the LLM model to be used for validation in LLM-as-a-Judge paradigm
    llm_name: str

    # List of rubrics to be evaluated during the reflection process
    rubric_names: list[Rubric]