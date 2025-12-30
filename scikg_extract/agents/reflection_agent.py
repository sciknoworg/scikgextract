"""
Reflection Agent for validating extracted structured processes using LLM-as-a-Judge paradigm.

This module defines a reflection agent that validates the extracted structured knowledge from the scientific documents using the provided rubrics like Correctness, Completeness, etc. The agent is implemented using langgraph's StateGraph to create a workflow that evaluates the extracted data against each rubric.
"""
# External imports
from langgraph.graph import StateGraph, START, END

# Scikg_Extract Config Imports
from scikg_extract.config.evaluation.rubricConfig import get_rubric_config

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# Scikg_Extract Agent Imports
from scikg_extract.agents.states import ExtractionState

def validate_extracted_processes(state: ExtractionState) -> ExtractionState:
    """
    Validates the extracted structured knowledge using the validation agent designed with langgraph StateGraph.
    Args:
        state (ExtractionState): The current state of the extraction process containing necessary data.
    Returns:
        ExtractionState: The final state containing the evaluation results.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting Validation Agent...")

    # Create the state graph
    graph = StateGraph(ExtractionState)
    logger.debug("Created StateGraph for validation workflow.")

    # Adding nodes for each rubric evaluation
    for rubric in state.rubric_names:
        # Get the rubric name
        rubric_name = rubric.get_rubric_name()

        # Formulate the node name
        node_name = f"evaluate_extraction_{rubric_name.lower()}"

        # Get the corresponding rubric action function
        node_action = get_rubric_config(rubric_name).func_tool

        # Add the node to the graph
        graph.add_node(node_name, node_action)
        logger.debug(f"Added node for evaluating extraction: {rubric_name}.")

    # Define the edges of the graph
    previous_node = START
    for rubric in state.rubric_names:
        # Get the name of the rubric
        rubric_name = rubric.get_rubric_name()

        # Formulate the node name
        node_name = f"evaluate_extraction_{rubric_name.lower()}"

        # Add edge from previous node to current node
        graph.add_edge(previous_node, node_name)
        logger.debug(f"Added edge from {previous_node} to {node_name}.")

        # Update the previous node
        previous_node = node_name
    
    # Add edge from last rubric node to END
    graph.add_edge(previous_node, END)
    logger.debug(f"Added edge from {previous_node} to END.")
    logger.debug("Defined edges for the validation workflow.")

    # Compile the graph
    validation_workflow = graph.compile()
    logger.debug("Compiled the validation workflow graph.")

    # Execute the validation workflow
    logger.info("Executing the validation workflow...")
    final_state = validation_workflow.invoke(state)

    # Return the final state with evaluation results
    return final_state