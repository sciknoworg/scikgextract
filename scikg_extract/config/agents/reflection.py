"""
ReflectionConfig dataclass for configuring the LLM-as-a-Judge reflection step.

Specifies which rubrics to evaluate, which judge LLMs to use, the reflection mode (single / multi-judge / debate), and related hyper-parameters such as the maximum number of debate iterations and the summarizer/critic LLMs.
"""
# Python imports
from dataclasses import dataclass, field

# External imports
from yescieval.base.rubric import Rubric

@dataclass
class ReflectionConfig:
    """
    Configuration dataclass for the Reflection Agent to be used in validating extracted structured knowledge using LLM-as-a-Judge paradigm.
    """
    
    # Reflection Mode
    reflection_mode: str
    
    # LLM to be used by reflection agent (e.g., "OPENAI:gpt-4o")
    reflection_llm: str

    # List of rubrics to be evaluated during the reflection process
    rubric_names: list[Rubric]

    # Summarizer LLM (e.g., "OPENAI:gpt-4o")
    summarizer_llm: str = ""

    # List of judge LLMs for multi-judge and debate modes (e.g., ["OPENAI:gpt-4o", "SAIA:llama-3.3-70b"])
    reflection_judge_llms: list[str] = field(default_factory=list)

    # List of critic LLMs for debate mode (e.g., ["OPENAI:gpt-4o"])
    reflection_critic_llms: list[str] = field(default_factory=list)

    # Debate max iterations (for debate mode)
    debate_max_iterations: int = 3