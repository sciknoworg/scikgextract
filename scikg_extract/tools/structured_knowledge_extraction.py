import json

from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.agents.states import ExtractionState
from scikg_extract.models.openai_adapter import Openai_Adapter
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

    # Initialize the OpenAI client
    openai_adapter = Openai_Adapter(model_name=state["llm_model"], temperature=0.1, response_format="json_object")
    logger.debug(f"Initialized Model adapter: {openai_adapter}")

    # Format the prompt template
    var_dict = {"process_name": state["process_name"], "process_description": state["process_description"], "scientific_document": state["scientific_document"], "schema": json.dumps(state["process_schema"]), "examples": state["examples"]}
    logger.debug(f"Prompt variables: {var_dict}")

    # Extract the knowledge
    extracted_info = openai_adapter.structured_completion(structure_knowledge_extraction, var_dict, state["data_model"])
    logger.debug(f"Extracted information: {extracted_info}")
    logger.info("Structured knowledge extraction completed.")

    # Update the state with the extracted JSON
    state["extracted_json"] = json.loads(extracted_info.model_dump_json())

    # Return the updated state with extracted JSON
    return state