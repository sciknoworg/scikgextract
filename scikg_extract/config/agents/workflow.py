# Python imports
from dataclasses import dataclass

@dataclass
class WorkflowConfig:
    """
    Configuration dataclass for the Orchestrator Agent for managing the overall extraction workflow.
    """

    # Normalize extracted data
    normalize_extracted_data: bool

    # Clean extracted data
    clean_extracted_data: bool

    # Validate extracted data
    validate_extracted_data: bool

    # Total retries for validation failures
    total_validation_retries: int = 3
