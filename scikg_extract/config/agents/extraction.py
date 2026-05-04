"""
ExtractionConfig dataclass for configuring the structured knowledge extraction step.

Specifies the LLM, output schema (Pydantic model), prompt templates, and any domain-specific parameters used by the extraction agent when invoking the LLM to produce structured knowledge from scientific text.
"""
# Python imports
from dataclasses import dataclass

# External imports
from pydantic import BaseModel

@dataclass
class ExtractionConfig:
    """
    Configuration Dataclass for the Extraction Agent to be used in extracting structured knowledge from scientific documents.
    """

    # LLM model name to be used by extraction agent
    llm_name: str

    # LLM model name for Normalization disambiguation
    normalization_llm_name: str

    # Pydantic data model for the extracted knowledge
    extraction_data_model: BaseModel

    # Synonym to CID Mapping
    synonym_to_cid_mapping: dict

    # PubChem LMDB Path
    pubchem_lmdb_path: str 

    # Properties to include for normalization
    normalization_properties_to_include: list[str]

    # Properties to exclude from normalization
    normalization_properties_to_exclude: list[str]