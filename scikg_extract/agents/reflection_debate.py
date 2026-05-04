"""
Debate-Based Reflection Agent for validating extracted structured processes through evaluator-critic debates.

This module defines a debate reflection subgraph where each rubric is evaluated through a structured debate between evaluator-critic pairs. Each evaluator produces an initial evaluation, then a critic challenges it. The evaluator can revise based on the critique. This process repeats until the critic is satisfied or the maximum number of debate iterations is reached. A summarizer then consolidates the final evaluations from all pairs into a single authoritative rating and rationale per rubric.
"""
# External Imports
from langgraph.graph import StateGraph, START, END

# SciKGExtract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# SciKGExtract Agent Imports
from scikg_extract.agents.states import ExtractionState

# SciKGExtract Debate and Summarization Tools
from scikg_extract.tools.evaluation.debate_evaluate import debate_evaluate_rubric
from scikg_extract.tools.evaluation.summarize_evaluations import summarize_rubric_evaluations

def validate_extracted_processes_debate(state: ExtractionState) -> ExtractionState:
    """
    Validates extracted structured knowledge using a debate-based approach. Each rubric is evaluated through structured evaluator-critic debates, then a summarizer consolidates the final evaluations from all pairs into a single rating and rationale per rubric.
    Args:
        state (ExtractionState): The current state containing extracted data, judge/critic configurations, and debate settings.
    Returns:
        ExtractionState: The final state with consolidated evaluation_results from all rubrics.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting Debate-Based Reflection Agent...")

    # Create the state graph
    graph = StateGraph(ExtractionState)
    logger.debug("Created StateGraph for debate validation workflow.")

    # Build nodes: for each rubric, add a debate evaluation node and a summarization node
    previous_node = START
    for rubric in state.rubric_names:
        rubric_name = rubric.get_rubric_name()

        # Debate evaluation node (runs all evaluator-critic pairs for this rubric)
        debate_node_name = f"debate_evaluate_{rubric_name.lower()}"
        debate_action = debate_evaluate_rubric(rubric_name)
        graph.add_node(debate_node_name, debate_action)
        logger.debug(f"Added debate evaluation node: {debate_node_name}")

        # Summarization node (consolidates debate results into a single evaluation)
        summarize_node_name = f"summarize_{rubric_name.lower()}_evaluations"
        summarize_action = summarize_rubric_evaluations(rubric_name)
        graph.add_node(summarize_node_name, summarize_action)
        logger.debug(f"Added summarization node: {summarize_node_name}")

        # Wire edges: previous → debate → summarize
        graph.add_edge(previous_node, debate_node_name)
        graph.add_edge(debate_node_name, summarize_node_name)
        logger.debug(f"Added edges: {previous_node} → {debate_node_name} → {summarize_node_name}")

        # The summarization node becomes the previous node for the next rubric
        previous_node = summarize_node_name

    # Wire the last summarization node to END
    graph.add_edge(previous_node, END)
    logger.debug(f"Added edge: {previous_node} → END")

    # Compile and execute the workflow
    debate_workflow = graph.compile()
    logger.info("Compiled debate validation workflow. Executing...")

    # Clear individual evaluation results before starting the workflow
    state.individual_evaluation_results = []

    # Execute the workflow with the initial state and get the final state with consolidated evaluation results
    final_state = debate_workflow.invoke(state)
    logger.info("Debate-Based Reflection Agent completed.")

    # Return the final state containing consolidated evaluation results for all rubrics
    return final_state