"""
Orchestrator Agent for managing the overall extraction workflow including structured knowledge extraction and LLM-as-a-Judge validation.

This module defines an orchestrator agent that manages the end-to-end workflow for extracting structured knowledge from scientific documents. It integrates the Extraction Agent for knowledge extraction and the Reflection Agent for validating the extracted data using specified rubrics.

Author: Sameer Sadruddin
Created: November 26, 2025
Last Modified: November 26, 2025
"""
# External imports
from langgraph.graph import StateGraph, START, END
from yescieval.base.rubric import Rubric

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# Scikg_Extract Config Imports
from scikg_extract.config.agents.orchestrator import OrchestratorConfig
from scikg_extract.config.agents.workflow import WorkflowConfig
from scikg_extract.config.agents.extraction import ExtractionConfig
from scikg_extract.config.agents.reflection import ReflectionConfig
from scikg_extract.config.process.processConfig import ProcessConfig
from scikg_extract.config.normalization.normalizationConfig import NormalizationConfig
from scikg_extract.config.llm.llmConfig import LLM_REGISTRY

# Scikg_Extract Agent Imports
from scikg_extract.agents.extraction_agent import extract_knowledge
from scikg_extract.agents.reflection_agent import validate_extracted_processes
from scikg_extract.agents.states import ExtractionState

def validate_orchestrator_config_params(orchestrator_config: OrchestratorConfig, workflowConfig: WorkflowConfig) -> bool:
    """
    Validates the parameters provided in the OrchestratorConfig.
    Args:
        orchestrator_config (OrchestratorConfig): Configuration for the Orchestrator Agent.
        workflowConfig (WorkflowConfig): Configuration for the overall extraction workflow.
    Returns:
        bool: True if all parameters are valid, otherwise raises ValueError.
    Raises:
        ValueError: If any of the required parameters are missing or invalid.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Validating Orchestrator Agent configuration parameters...")

    # Step 1: Validate LLM models (LLM model for extraction, reflection and feedback)
    if orchestrator_config.llm_name not in LLM_REGISTRY:
        raise ValueError(f"Extraction LLM model {orchestrator_config.llm_name} not found in registry.")
    logger.debug(f"LLM model for extraction: {orchestrator_config.llm_name} is valid.")
    
    if workflowConfig.validate_extracted_data:
        if orchestrator_config.reflection_llm_name not in LLM_REGISTRY:
            raise ValueError(f"Reflection LLM model {orchestrator_config.reflection_llm_name} not found in registry.")
        logger.debug(f"LLM model for reflection: {orchestrator_config.reflection_llm_name} is valid.")

    # Step 2: Check that process schema, scientific document are provided
    if not orchestrator_config.process_schema:
        raise ValueError("Process schema is missing in the Orchestrator configuration.")
    if not orchestrator_config.scientific_document:
        raise ValueError("Scientific document is missing in the Orchestrator configuration.")
    logger.debug("Process schema and scientific document are provided.")
    
    # Step 3: Check if LLM-as-a-Judge rubrics (at least one) are provided if validation is enabled
    if workflowConfig.validate_extracted_data:
        if not orchestrator_config.rubrics:
            raise ValueError("At least one rubric must be provided for LLM-as-a-Judge validation in the Orchestrator configuration.")
        logger.debug("At least one rubric is provided for LLM-as-a-Judge validation.")

    # Step 4: Check if all Rubrics are of type Rubric from yescieval if validation is enabled
    if workflowConfig.validate_extracted_data:
        valid_rubrics = all(isinstance(rubric, Rubric) for rubric in orchestrator_config.rubrics)
        if not valid_rubrics:
            raise ValueError("All provided rubrics must be instances of the Rubric class from yescieval.")
        logger.debug("All provided rubrics are valid instances of the Rubric class.")

    # Return True if all validations pass
    return True


def orchestrate_extraction_workflow(orchestrator_config: OrchestratorConfig, workflow_config: WorkflowConfig) -> dict:
    """
    Orchestrates the overall extraction workflow containing structured knowledge extraction, LLM-as-a-Judge validation and exporting the final structured knowledge.
    Args:
        orchestrator_config (OrchestratorConfig): Configuration for the Orchestrator Agent.
        workflow_config (WorkflowConfig): Configuration for the overall extraction workflow.
    Returns:
        dict: The final extracted and validated structured knowledge as a dictionary.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting Orchestrator Agent for extraction workflow...")

    # Step 1: Validated the provided orchestrator configuration
    validate_orchestrator_config_params(orchestrator_config, workflow_config)
    logger.debug("Orchestrator configuration parameters are valid.")

    # Step 2: Initialize the state object for the extraction workflow
    state = {
        "process_name": ProcessConfig.Process_name,
        "process_description": ProcessConfig.Process_description,
        "process_property_constraints": ProcessConfig.Process_property_constraints,
        "process_schema": orchestrator_config.process_schema,
        "process_instances_key": "processes",
        "scientific_document": orchestrator_config.scientific_document,
        "examples": orchestrator_config.examples,
        "evaluation_results": None,
        "user_feedback_prompt": None
    }
    state = ExtractionState(**state)

    # Step 3: Extract structured knowledge using Extraction Agent
    # Update Normalization Config if normalization is enabled in workflow config
    if workflow_config.normalize_extracted_data:
        NormalizationConfig.pubchem_lmdb_path = orchestrator_config.pubchem_lmdb_path
        NormalizationConfig.synonym_to_cid_mapping = orchestrator_config.synonym_to_cid_mapping

    # Setup Extraction Config
    extractionConfig = ExtractionConfig(
        llm_name=orchestrator_config.llm_name,
        extraction_data_model=orchestrator_config.extraction_data_model,
        synonym_to_cid_mapping=orchestrator_config.synonym_to_cid_mapping,
        pubchem_lmdb_path=orchestrator_config.pubchem_lmdb_path,
        normalization_properties_to_include=NormalizationConfig.include_paths,
        normalization_properties_to_exclude=NormalizationConfig.exclude_paths
    )

    # Invoke the extraction agent
    state = extract_knowledge(extractionConfig, state, workflow_config)
    logger.debug("Structured knowledge extraction completed.")

    # Step 4: Validate the extracted structured knowledge using Reflection Agent if enabled in workflow config
    if workflow_config.validate_extracted_data:
        
        # Setup Reflection Config
        reflectionConfig = ReflectionConfig(
            llm_name=orchestrator_config.reflection_llm_name,
            rubrics=orchestrator_config.rubrics
        )

        # Invoke the reflection agent for validation
        state = validate_extracted_processes(reflectionConfig, state)
        logger.debug("LLM-as-a-Judge validation completed.")

    # Step 5: Return the final extracted and validated structured knowledge
    return state["extracted_json"]