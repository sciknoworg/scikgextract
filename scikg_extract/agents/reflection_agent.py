"""
Reflection Agent for validating extracted structured processes using LLM-as-a-Judge paradigm.

This module defines a reflection agent that validates the extracted structured knowledge from the scientific documents using the provided rubrics like Correctness, Completeness, etc. The agent supports three reflection modes:
- single: Sequential single-judge evaluation per rubric (default behavior).
- multi-judge: Multiple LLM judges evaluate each rubric independently, then a summarizer consolidates.
- debate: Evaluator-critic pairs debate each rubric, then a summarizer consolidates.

The mode is determined by state.reflection_mode, which is set from the REFLECTION_MODE env var or overridden in OrchestratorConfig.
"""
# External imports
from langgraph.graph import StateGraph, START, END

# Scikg_Extract Config Imports
from scikg_extract.config.evaluation.rubricConfig import get_rubric_config

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# Scikg_Extract Agent Imports
from scikg_extract.agents.states import ExtractionState
from scikg_extract.agents.reflection_multi_judge import validate_extracted_processes_multi_judge
from scikg_extract.agents.reflection_debate import validate_extracted_processes_debate

def validate_extracted_processes(state: ExtractionState) -> ExtractionState:
    """
    Validates the extracted structured knowledge by routing to the appropriate reflection
    mode based on state.reflection_mode.
    Args:
        state (ExtractionState): The current state of the extraction process containing necessary data.
    Returns:
        ExtractionState: The final state containing the evaluation results.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    mode = state.reflection_mode.lower().strip()
    logger.info(f"Starting Validation Agent (mode: {mode})...")

    if mode == "multi-judge":
        return validate_extracted_processes_multi_judge(state)
    elif mode == "debate":
        return validate_extracted_processes_debate(state)
    else:
        # Default: single-judge mode (original behavior)
        if mode != "single":
            logger.warning(f"Unknown reflection mode '{mode}'. Falling back to 'single' mode.")
        return _validate_single(state)

def _validate_single(state: ExtractionState) -> ExtractionState:
    """
    Validates the extracted structured knowledge using a single-judge approach with langgraph StateGraph. This is the original behavior where each rubric is evaluated sequentially by a single LLM judge.
    Args:
        state (ExtractionState): The current state of the extraction process containing necessary data.
    Returns:
        ExtractionState: The final state containing the evaluation results.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Running single-judge validation workflow...")

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