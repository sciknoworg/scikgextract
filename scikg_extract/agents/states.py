"""
Extraction state definition for the SciKGExtract agent workflow.

This module defines ExtractionState, the central Pydantic model that is threaded through every node in the LangGraph workflow. It holds all inputs, intermediate results, and final outputs produced across the extraction, reflection, and feedback phases of the pipeline.
"""
# Pydantic Imports
from typing import Any
from pydantic import BaseModel, Field

from yescieval.base.rubric import Rubric

class ExtractionState(BaseModel):
    """
    State for the knowledge extraction agent workflow. It holds the updated structured knowledge and relevant metadata at each step of the extraction process.
    """

    ##############################
    # Extraction Agent properties #
    ##############################

    # LLM to be used by extraction agent
    extraction_llm: str

    # Process Name
    process_name: str

    # Process Description
    process_description: str

    # Process Property Constraints
    process_property_constraints: str

    # Process Schema
    process_schema: dict

    # Key containing process instances
    process_instances_key: str

    # Scientific Document
    scientific_document: str

    # Process Examples
    examples: str

    # Pydantic Data Model
    data_model: type[BaseModel]

    # Extracted JSON
    extracted_json: dict = Field(default_factory=dict)

    # Normalized JSON
    normalized_json: dict = Field(default_factory=dict)

    # Extracted JSOn Valid
    extraction_json_valid: bool = False

    # Normalize Extracted JSON
    normalize_extracted_json: bool = False

    # Clean Extracted JSON
    cleaned_extracted_json: bool = False

    # LLM to be used for normalization within extraction agent
    normalization_llm: str = ""

    # PubChem LMDB Path
    pubchem_lmdb_path: str = ""

    # Synonym to CID Mapping
    synonym_to_cid_mapping: dict = Field(default_factory=dict)

    # Normalization Properties to Include
    normalization_properties_to_include: list[str] = Field(default_factory=list)

    # Normalization Properties to Exclude
    normalization_properties_to_exclude: list[str] = Field(default_factory=list)

    ##############################
    # Reflection Agent properties #
    ##############################

    # Reflection Mode
    reflection_mode: str = "single"

    # LLM to be used by reflection agent in single judge mode
    reflection_llm: str = ""

    # LLM to be used by summarizer in reflection agent
    summarizer_llm: str = ""

    # List of judge LLMs for multi-judge and debate modes (e.g., ["OPENAI:gpt-4o", "SAIA:llama-3.3-70b"])
    reflection_judge_llms: list[str] = Field(default_factory=list)

    # List of critic LLMs for debate mode (e.g., ["OPENAI:gpt-4o"])
    reflection_critic_llms: list[str] = Field(default_factory=list)

    # Validation Rubrics
    rubric_names: list[type[Rubric]] = Field(default_factory=list)

    # Evaluation Results from LLM-as-a-Judge
    evaluation_results: dict[str, dict[str, str]] | None = None

    # Individual evaluation results per judge (for multi-judge and debate modes)
    individual_evaluation_results: list[dict[str, Any]] = Field(default_factory=list)

    # Total retries for validation failures
    total_validation_retries: int = 3

    # Debate max iterations
    debate_max_iterations: int = 3

    ###############################
    # Feedback Agent properties #
    ###############################

    # LLM to be used by feedback agent
    feedback_llm: str = ""

    # User prompt with feedback
    user_feedback_prompt: str | None = ""