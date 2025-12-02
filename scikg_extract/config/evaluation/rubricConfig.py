# Python imports
from dataclasses import dataclass

# Scikg_Extract Evalution rubric Imports
from scikg_extract.evaluation.rubrics.informativeness import Correctness
from scikg_extract.evaluation.rubrics.informativeness import Completeness

# Scikg_Extract Evalution tool Imports
from scikg_extract.tools.evaluation.evaluate_extraction import evaluate_extraction_correctness
from scikg_extract.tools.evaluation.evaluate_extraction import evaluate_extraction_completeness

# Data model for Evaluation Ratings
from data.models.evaluation.evaluation_rating import EvaluationRating

# External imports
from yescieval.base.rubric import Rubric

@dataclass
class RubricConfig:
    """
    Configuration dataclass class for Rubrics to be used in the evaluation of structured knowledge extraction.
    """
    rubric_class: type[Rubric]
    data_model: EvaluationRating
    func_tool: callable
    enabled: bool = True

# Registry of available Rubrics/Metrics
RUBRICS_REGISTRY = {
    "Correctness": RubricConfig(
        rubric_class=Correctness,
        data_model=EvaluationRating,
        func_tool=evaluate_extraction_correctness,
        enabled=True
    ),
    "Completeness": RubricConfig(
        rubric_class=Completeness,
        data_model=EvaluationRating,
        func_tool=evaluate_extraction_completeness,
        enabled=True
    )
}

def get_enabled_rubrics() -> dict[str, RubricConfig]:
    """
    Retrieves the enabled rubrics from the registry.
    Returns:
        dict[str, RubricConfig]: A dictionary of enabled rubric configurations.
    """
    return {name: config for name, config in RUBRICS_REGISTRY.items() if config.enabled}

def check_rubric_present(rubric_name: str) -> bool:
    """
    Checks if a specific rubric is present in the registry.
    Args:
        rubric_name (str): The name of the rubric to check.
    Returns:
        bool: True if the rubric is present, False otherwise.
    """
    return rubric_name in RUBRICS_REGISTRY

def get_rubric_config(rubric_name: str) -> RubricConfig:
    """
    Retrieves the configuration for a specific rubric by name.
    Args:
        rubric_name (str): The name of the rubric.
    Returns:
        RubricConfig: The configuration of the specified rubric.
    """
    # Check if the rubric is present
    if not check_rubric_present(rubric_name):
        raise ValueError(f"Rubric '{rubric_name}' is not present in the registry.")
    return RUBRICS_REGISTRY[rubric_name]

