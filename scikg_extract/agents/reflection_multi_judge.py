"""
Multi-Judge Reflection Agent for validating extracted structured processes using multiple LLM judges.

This module defines a multi-judge reflection subgraph where each rubric is evaluated by multiple LLM judges independently. After all judges have evaluated a rubric, a summarizer consolidates the individual evaluations into a single authoritative rating and rationale per rubric.
"""
# External Imports
from langgraph.graph import StateGraph, START, END

# SciKGExtract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# SciKGExtract Agent Imports
from scikg_extract.agents.states import ExtractionState

# SciKGExtract Multi-Judge Tools
from scikg_extract.tools.evaluation.multi_judge_evaluate import multi_judge_evaluate_rubric
from scikg_extract.tools.evaluation.summarize_evaluations import summarize_rubric_evaluations

def validate_extracted_processes_multi_judge(state: ExtractionState) -> ExtractionState:
    """
    Validates extracted structured knowledge using a multi-judge approach. Multiple LLM judges independently evaluate each rubric, then a summarizer consolidates their evaluations into a single rating and rationale per rubric.
    Args:
        state (ExtractionState): The current state containing extracted data and judge configurations.
    Returns:
        ExtractionState: The final state with consolidated evaluation_results from all rubrics.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting Multi-Judge Reflection Agent...")

    # Create the state graph
    graph = StateGraph(ExtractionState)
    logger.debug("Created StateGraph for multi-judge validation workflow.")

    # Build nodes: for each rubric, add a multi-judge evaluation node and a summarization node
    previous_node = START
    for rubric in state.rubric_names:
        rubric_name = rubric.get_rubric_name()

        # Multi-judge evaluation node
        eval_node_name = f"multi_judge_evaluate_{rubric_name.lower()}"
        eval_action = multi_judge_evaluate_rubric(rubric_name)
        graph.add_node(eval_node_name, eval_action)
        logger.debug(f"Added multi-judge evaluation node: {eval_node_name}")

        # Summarization node
        summarize_node_name = f"summarize_{rubric_name.lower()}_evaluations"
        summarize_action = summarize_rubric_evaluations(rubric_name)
        graph.add_node(summarize_node_name, summarize_action)
        logger.debug(f"Added summarization node: {summarize_node_name}")

        # Wire edges: previous → evaluate → summarize
        graph.add_edge(previous_node, eval_node_name)
        graph.add_edge(eval_node_name, summarize_node_name)
        logger.debug(f"Added edges: {previous_node} → {eval_node_name} → {summarize_node_name}")

        # The summarization node becomes the previous node for the next rubric
        previous_node = summarize_node_name

    # Wire the last summarization node to END
    graph.add_edge(previous_node, END)
    logger.debug(f"Added edge: {previous_node} → END")

    # Compile and execute the workflow
    multi_judge_workflow = graph.compile()
    logger.info("Compiled multi-judge validation workflow. Executing...")

    # Clear individual evaluation results before starting the workflow
    state.individual_evaluation_results = []

    # Execute the workflow with the initial state and get the final state with consolidated evaluation results
    final_state = multi_judge_workflow.invoke(state)
    logger.info("Multi-Judge Reflection Agent completed.")

    # Return the final state containing consolidated evaluation results for all rubrics
    return final_state