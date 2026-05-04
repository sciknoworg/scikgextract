"""
WorkflowConfig dataclass for controlling LangGraph workflow execution settings.

Defines iteration limits, reflection modes, and toggles for normalization, cleaning, validation, and refinement steps within the orchestrator agent's management of the structured knowledge extraction workflow.
"""
# Python imports
from dataclasses import dataclass

# SciKGExtract Config Imports
from scikg_extract.config.llm.envConfig import EnvConfig

@dataclass
class WorkflowConfig:
    """
    Configuration dataclass for the Orchestrator Agent for managing the overall extraction workflow.
    """

    # Normalize extracted data
    normalize_extracted_data: bool = EnvConfig.NORMALIZE_EXTRACTED_KNOWLEDGE

    # Clean extracted data
    clean_extracted_data: bool = EnvConfig.CLEAN_EXTRACTED_KNOWLEDGE

    # Validate extracted data
    validate_extracted_data: bool = EnvConfig.VALIDATE_EXTRACTED_KNOWLEDGE

    # Refine extracted data
    refine_extracted_data: bool = EnvConfig.REFINE_EXTRACTED_KNOWLEDGE

    # Reflection mode
    reflection_mode: str = EnvConfig.REFLECTION_MODE

    # Total retries for validation failures
    total_validation_retries: int = EnvConfig.TOTAL_REFINEMENT_ITERATIONS

    # Debate max iterations (for debate mode)
    debate_max_iterations: int = EnvConfig.DEBATE_MAX_ITERATIONS
