# Python imports
from dataclasses import dataclass

# External imports
from pydantic import BaseModel
from yescieval.base.rubric import Rubric

@dataclass
class OrchestratorConfig:
    """
    Configuration dataclass for the Orchestrator Agent to be used in managing the overall extraction workflow.
    """
    
    #######################################
    # Configurations for Extraction Agent #
    #######################################
    
    # LLM model name to be used by extraction agent
    llm_name: str

    # Process Schema defining the structure of the extraction
    process_schema: dict

    # Scientific Document in markdown format for extraction
    scientific_document: str

    # Domain expert provided examples to guide the extraction
    examples: str

    # Pydantic data model for the extracted knowledge
    extraction_data_model: BaseModel

    # PubChem LMDB Path
    pubchem_lmdb_path: str

    # Synonym to CID Mapping
    synonym_to_cid_mapping: dict

    #######################################
    # Configurations for Reflection Agent #
    #######################################

    # LLM model name to be used by reflection agent
    reflection_llm_name: str

    # List of rubrics to be evaluated during reflection
    rubrics: list[Rubric]

    #####################################
    # Configurations for Feedback Agent #
    #####################################

    # LLM model name to be used by feedback agent
    feedback_llm_name: str