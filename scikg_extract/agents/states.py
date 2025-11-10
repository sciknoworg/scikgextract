from typing import TypedDict
from pydantic import BaseModel

class ExtractionState(TypedDict):
    """
    State for the knowledge extraction agent workflow. It holds the updated structured knowledge and relevant metadata at each step of the extraction process.
    """

    # Largest Language Model Name
    llm_model: str

    # Process Name
    process_name: str

    # Process Description
    process_description: str

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