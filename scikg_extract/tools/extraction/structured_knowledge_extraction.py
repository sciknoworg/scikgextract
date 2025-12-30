"""
Structured Knowledge Extraction Tools using Large Language Models (LLMs) and process Schema.

The module defines tools for extracting and refining structured knowledge from scientific documents based on provided process schema and examples. The extraction tool utilizes LLMs to generate structured data, while the refinement tool allows for updating the extracted knowledge based on feedback.

Author: Sameer Sadruddin
Created: November 21, 2025
Last Modified: November 27, 2025
"""
# Python imports
import json
from types import SimpleNamespace

# Scikg_Extract Config Imports
from scikg_extract.config.llm.llmConfig import LLM_REGISTRY

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# Scikg_Extract Agent Imports
from scikg_extract.agents.states import ExtractionState

# Scikg_Extract Prompt Imports
from scikg_extract.prompts.tools import structure_knowledge_extraction

def structured_knowledge_extraction(state: ExtractionState) -> ExtractionState:
    """
    Extracts structured knowledge from a scientific document using a language model based on the provided schema and examples.
    Args:
        state (ExtractionState): The current state of the extraction process containing necessary inputs.
    Returns:
        ExtractionState: The updated state with the extracted structured knowledge.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting structured knowledge extraction tool...")

    # Initialize the model adapter
    inference_adapter = LLM_REGISTRY.get(state.llm_model).inference_adapter
    model_adapter = inference_adapter(model_name=state.llm_model, temperature=0.1, response_format="json_object")
    logger.debug(f"Initialized Model adapter: {model_adapter}")

    # Format the prompt template
    var_dict = {"process_name": state.process_name, "process_description": state.process_description, "process_property_constraints": state.process_property_constraints, "scientific_document": state.scientific_document, "schema": json.dumps(state.process_schema), "examples": state.examples}

    # Extract the knowledge
    extracted_info = model_adapter.structured_completion(structure_knowledge_extraction, var_dict, state.data_model)
    logger.debug("Structured knowledge extraction completed.")

    # Update the state with the extracted JSON
    state.extracted_json = json.loads(extracted_info.model_dump_json())
    logger.debug("Updated state with extracted JSON.")

    # Return the updated state with extracted JSON
    return state

def refine_extracted_knowledge(state: ExtractionState) -> ExtractionState:
    """
    Refines the extracted structured knowledge based on the feedback provided by the Reflection Agent using LLM-as-a-judge approach.
    Args:
        state (ExtractionState): The current state of the extraction process containing necessary inputs.
    Returns:
        ExtractionState: The updated state with the refined structured knowledge.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting refinement of extracted structured knowledge...")

    # Initialize the model adapter
    inference_adapter = LLM_REGISTRY.get(state.llm_model).inference_adapter
    model_adapter = inference_adapter(model_name=state.llm_model, temperature=0.1, response_format="json_object")
    logger.debug(f"Initialized Model adapter: {model_adapter}")

    # Format the prompt template
    var_dict = {"process_name": state.process_name, "process_description": state.process_description, "process_property_constraints": state.process_property_constraints, "scientific_document": state.scientific_document, "schema": json.dumps(state.process_schema), "examples": state.examples}

    # Update the user prompt now containing the feedback from Reflection Agent
    updated_user_prompt = state.user_feedback_prompt
    prompt_template = SimpleNamespace(
        system_prompt=structure_knowledge_extraction.system_prompt,
        user_prompt=updated_user_prompt
    )
    logger.debug(f"Formatted user prompt for refinement:\n{updated_user_prompt}\n")

    # Extract the knowledge
    extracted_info = model_adapter.structured_completion(prompt_template, var_dict, state.data_model)
    logger.info("Structured knowledge extraction completed.")

    # Update the state with the extracted JSON
    state.extracted_json = json.loads(extracted_info.model_dump_json())
    logger.debug("Updated state with refined extracted JSON.")

    # Update the retry count for refinement
    state.total_validation_retries -= 1
    logger.debug(f"Decremented total_validation_retries to {state.total_validation_retries}.")

    # Return the updated state with extracted JSON
    return state