"""
OrchestratorConfig dataclass for configuring the end-to-end SciKG-Extract pipeline.

This module defines OrchestratorConfig, a dataclass that aggregates all configuration needed to run the extraction, reflection, normalization, and feedback phases. It is the single object passed to the orchestrator agent when building and running the LangGraph workflow.
"""
# Python imports
from dataclasses import dataclass, field

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
    
    # LLM to be used by extraction agent
    extraction_llm: str

    # Process Schema defining the structure of the extraction
    process_schema: dict

    # Scientific Document in markdown format for extraction
    scientific_document: str

    # Domain expert provided examples to guide the extraction
    examples: str

    # Pydantic data model for the extracted knowledge
    extraction_data_model: BaseModel

    # LLM to be used for normalization within extraction agent
    normalization_llm: str = ""

    # PubChem LMDB Path
    pubchem_lmdb_path: str = ""

    # Synonym to CID Mapping
    synonym_to_cid_mapping: dict = field(default_factory=dict)

    #######################################
    # Configurations for Reflection Agent #
    #######################################

    # LLM to be used by reflection agent
    reflection_llm: str = ""

    # LLM to be used by summarizer in reflection agent
    summarizer_llm: str = ""

    # List of judge LLMs for multi-judge and debate modes (e.g., ["OPENAI:gpt-4o", "SAIA:llama-3.3-70b"])
    reflection_judge_llms: list[str] = field(default_factory=list)

    # List of critic LLMs for debate mode (e.g., ["OPENAI:gpt-4o"])
    reflection_critic_llms: list[str] = field(default_factory=list)

    # List of rubrics to be evaluated during reflection
    rubrics: list[type[Rubric]] = field(default_factory=list)

    #####################################
    # Configurations for Feedback Agent #
    #####################################

    # LLM to be used by feedback agent
    feedback_llm: str = ""