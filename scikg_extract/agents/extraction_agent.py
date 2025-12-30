"""
Extraction Agent for Structured Knowledge Extraction using Large Language Models (LLMs), process Schema and normalization with PubChem.

The module defines an extraction agent which extracts and structure knowledge from scientific documents based on provided process schema and examples. It also optionally, normalizes the predifined properties in the extracted knowledge using PubChem database. The agent is implemented using langgraph's StateGraph to create a workflow that performs extraction, validation, normalization and cleaning of the structured knowledge.
"""
# External imports
from langgraph.graph import StateGraph, START, END

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# Scikg_Extract Agent Imports
from scikg_extract.agents.states import ExtractionState

# Scikg_Extract Tool Imports
from scikg_extract.tools.extraction.json_cleaner import json_cleaner
from scikg_extract.tools.extraction.json_validator import json_validator
from scikg_extract.tools.extraction.structured_knowledge_extraction import structured_knowledge_extraction
from scikg_extract.tools.extraction.pubchem_normalization import pubchem_normalization
from scikg_extract.tools.extraction.structured_knowledge_extraction import refine_extracted_knowledge

def tool_for_extraction(state: ExtractionState) -> tuple[str, callable]:
    """
    Determines the appropriate tool function for structured knowledge extraction based on the current state. Either performs initial extraction or refines existing extraction based on feedback.
    Args:
        state (ExtractionState): The current state of the extraction process containing necessary data.
    Returns:
        tuple[str, callable]: The name and function of the tool to be used for extraction.
    """
    if state.user_feedback_prompt and state.evaluation_results:
        return ("refine_extracted_knowledge", refine_extracted_knowledge)
    else:
        return ("structured_knowledge_extraction", structured_knowledge_extraction)

def extract_knowledge(state: ExtractionState) -> ExtractionState:
    """
    Extracts structured knowledge from a scientific document using the extraction agent designed with langgraph StateGraph.
    Args:
        state (ExtractionState): The current state of the extraction process.
    Returns:
        ExtractionState: The final state containing the extracted structured knowledge.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting knowledge extraction agent...")

    # Create the state graph
    graph = StateGraph(ExtractionState)
    logger.debug("Created StateGraph for the extraction agent.")

    # Create a list to hold the nodes
    nodes: list[str] = []

    # Determine the extraction tool based on the current state
    extraction_tool_name, extraction_tool_func = tool_for_extraction(state)
    logger.debug(f"Determined extraction tool: {extraction_tool_name}.")

    # Add node for structured knowledge extraction tool
    graph.add_node(extraction_tool_name, extraction_tool_func)
    nodes.append(extraction_tool_name)
    logger.debug(f"Added {extraction_tool_name} node to the graph.")

    # Add node for JSON validation
    graph.add_node("json_validator", json_validator)
    nodes.append("json_validator")
    logger.debug("Added json_validator node to the graph.")

    # Add node for PubChem normalization if enabled in workflowConfig
    if state.normalize_extracted_json:
        graph.add_node("pubchem_normalization", pubchem_normalization)
        nodes.append("pubchem_normalization")
        logger.debug("Added pubchem_normalization node to the graph.")

    # Add node for JSON cleaning if enabled in workflowConfig
    if state.cleaned_extracted_json:
        graph.add_node("json_cleaner", json_cleaner)
        nodes.append("json_cleaner")
        logger.debug("Added json_cleaner node to the graph.")

    # Define the edges of the graph
    previous_node = START
    for node in nodes:
        graph.add_edge(previous_node, node)
        logger.debug(f"Added edge from {previous_node} to {node}.")
        previous_node = node
    graph.add_edge(previous_node, END)
    logger.debug(f"Added edge from {previous_node} to END.")
    logger.debug(f"Defined edges for the StateGraph. Graph Edges: {graph.edges}")

    # Compile the graph
    extraction_workflow = graph.compile()
    logger.debug("Compiled the StateGraph into a extraction workflow.")

    # Execute the workflow
    logger.info("Executing the extraction StateGraph for structured knowledge extraction...")
    final_state = extraction_workflow.invoke(state)

    # Return the final state with extracted structured knowledge
    return final_state