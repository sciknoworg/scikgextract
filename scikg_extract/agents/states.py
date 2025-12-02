# Python Imports
from typing import TypedDict

# Pydantic Imports
from pydantic import BaseModel

class ExtractionState(TypedDict):
    """
    State for the knowledge extraction agent workflow. It holds the updated structured knowledge and relevant metadata at each step of the extraction process.
    """

    ##############################
    # Extraction Agent properties #
    ##############################

    # Largest Language Model Name
    llm_model: str

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
    data_model: BaseModel

    # Extracted JSON
    extracted_json: dict

    # Extracted JSOn Valid
    extraction_json_valid: bool

    # PubChem LMDB Path
    pubchem_lmdb_path: str

    # Synonym to CID Mapping
    synonym_to_cid_mapping: dict

    # Normalization Properties to Include
    normalization_properties_to_include: list[str]

    # Normalization Properties to Exclude
    normalization_properties_to_exclude: list[str]

    ##############################
    # Reflection Agent properties #
    ##############################

    # Validation LLM Model
    validation_llm_model: str

    # Evaluation Results from LLM-as-a-Judge
    evaluation_results: dict[str, dict[str, str]]

    ###############################
    # Feedback Agent properties #
    ###############################

    # Feedback LLM Model
    feedback_llm_model: str

    # User prompt with feedback
    user_feedback_prompt: str