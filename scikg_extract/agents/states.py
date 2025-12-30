# Pydantic Imports
from pydantic import BaseModel, Field

from yescieval.base.rubric import Rubric

class ExtractionState(BaseModel):
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

    # LLM for Normalization Disambiguation
    normalization_llm_model: str = ""

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

    # Validation LLM Model
    validation_llm_model: str = ""

    # Validation Rubrics
    rubric_names: list[type[Rubric]] = Field(default_factory=list)

    # Evaluation Results from LLM-as-a-Judge
    evaluation_results: dict[str, dict[str, str]] | None = None

    # Total retries for validation failures
    total_validation_retries: int = 3

    ###############################
    # Feedback Agent properties #
    ###############################

    # Feedback LLM Model
    feedback_llm_model: str = ""

    # User prompt with feedback
    user_feedback_prompt: str | None = ""