from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END

from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.config.normalizationConfig import NormalizationConfig
from scikg_extract.agents.states import ExtractionState
from scikg_extract.tools.json_cleaner import json_cleaner
from scikg_extract.tools.json_validator import json_validator
from scikg_extract.tools.structured_knowledge_extraction import structured_knowledge_extraction

def extract_knowledge(llm_model: str, process_name: str, process_description: str, process_schema: dict, scientific_document: str, examples: str, data_model: BaseModel, pubchem_lmdb_path: str, synonym_to_cid_mapping: dict) -> dict:
    """
    Extracts structured knowledge from a scientific document using a knowledge extraction agent workflow desined with langgraph StateGraph.
    Args:
        llm_model (str): The name of the language model to use.
        process_name (str): The name of the scientific process.
        process_description (str): A brief description of the scientific process.
        process_schema (dict): The schema defining the structure of the knowledge to be extracted.
        scientific_document (str): The scientific document in markdown format.
        examples (str): Gold-standard examples to guide the extraction.
        data_model (BaseModel): The Pydantic data model for validation of the extracted knowledge.
        pubchem_lmdb_path (str): Path to the PubChem LMDB database for normalization.
        synonym_to_cid_mapping (dict): Manual curated PubChem synonym to CID mapping dictionary.
    Returns:
        dict: The extracted structured knowledge as a dictionary.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting knowledge extraction agent...")

    # Read the properties to normalize
    properties_to_normalize = NormalizationConfig.include_paths
    if not properties_to_normalize:
        logger.warning("No properties specified for normalization. Exiting.")
    logger.info(f"Total properties to normalize: {len(properties_to_normalize)}, Properties: {properties_to_normalize}")

    # Read the properties to exclude
    properties_to_exclude = NormalizationConfig.exclude_paths
    logger.info(f"Total properties to exclude from normalization: {len(properties_to_exclude)}, Properties: {properties_to_exclude}")

    # Define the initial state
    initial_state = {
        "llm_model": llm_model,
        "process_name": process_name,
        "process_description": process_description,
        "process_schema": process_schema,
        "scientific_document": scientific_document,
        "examples": examples,
        "data_model": data_model,
        "pubchem_lmdb_path": pubchem_lmdb_path,
        "synonym_to_cid_mapping": synonym_to_cid_mapping,
        "normalization_properties_to_include": properties_to_normalize,
        "normalization_properties_to_exclude": properties_to_exclude,
    }
    logger.debug(f"Extraction Agent - Initial State: {initial_state}")

    # Create the state graph
    graph = StateGraph(ExtractionState)
    logger.debug("Created StateGraph for extraction workflow.")

    # Add node for structured knowledge extraction
    graph.add_node("structured_knowledge_extraction", structured_knowledge_extraction)
    logger.debug("Added structured_knowledge_extraction node to the graph.")

    # Add node for JSON cleaning
    graph.add_node("json_cleaner", json_cleaner)
    logger.debug("Added json_cleaner node to the graph.")

    # Add node for JSON validation
    graph.add_node("json_validator", json_validator)
    logger.debug("Added json_validator node to the graph.")

    # Define the edges
    graph.add_edge(START, "structured_knowledge_extraction")
    graph.add_edge("structured_knowledge_extraction", "json_validator")
    graph.add_edge("json_validator", "json_cleaner")
    graph.add_edge("json_cleaner", END)
    logger.debug(f"Added edges between nodes in the graph.\n Graph Edges: {graph.edges}")

    # Compile the graph
    workflow = graph.compile()
    logger.debug("Compiled the StateGraph into a workflow.")

    # Execute the workflow
    logger.info("Executing the extraction StateGraph for structured knowledge extraction...")
    final_state = workflow.invoke(initial_state)
    logger.debug(f"Final State after extraction workflow: {final_state}")

    # Return the extracted structured knowledge as a Pydantic model
    extracted_info = final_state["extracted_json"]
    logger.debug(f"Extracted Information Model: {extracted_info}")

    # Return the extracted information
    return extracted_info