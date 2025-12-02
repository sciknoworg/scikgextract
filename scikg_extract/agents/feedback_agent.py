# External Imports
from langgraph.graph import StateGraph, START, END

# Scikg_Extract Config Imports
from scikg_extract.config.agents.feedback import FeedbackConfig
from scikg_extract.config.llm.llmConfig import LLM_REGISTRY

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# Scikg_Extract Agent Imports
from scikg_extract.agents.states import ExtractionState

# Scikg_Extract Tool Imports
from scikg_extract.tools.feedback.prompt_with_feedback import prompt_with_feedback

def provide_feedback(feedbackConfig: FeedbackConfig, state: ExtractionState) -> ExtractionState:
    """
    Provides the formatted user prompt with feedback on the extracted structured knowledge to be used for refining the extraction by the Extraction Agent.
    Args:
        feedbackConfig (FeedbackConfig): Configuration for the Feedback Agent.
        state (ExtractionState): The current state of the extraction process containing necessary data.
    Returns:
        ExtractionState: The final state containing user feedback prompt.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting Feedback Agent...")

    # Add the LLM model to be used for feedback generation
    state["feedback_llm_model"] = feedbackConfig.llm_name

    # Create the state graph
    graph = StateGraph(ExtractionState)
    logger.debug("Created StateGraph for feedback workflow.")

    # Add node for formatting prompt with feedback
    graph.add_node("prompt_with_feedback", prompt_with_feedback)
    logger.debug("Added prompt_with_feedback node to the graph.")

    # Define the edges of the graph
    graph.add_edge(START, "prompt_with_feedback")
    graph.add_edge("prompt_with_feedback", END)
    logger.debug("Defined edges for the feedback workflow graph.")

    # Compile the graph
    feedback_workflow = graph.compile()
    logger.info("Compiled the feedback workflow graph.")

    # Execute the feedback workflow
    logger.info("Invoking the feedback workflow...")
    final_state = feedback_workflow.invoke(state)

    # Return the final state with user feedback prompt
    return final_state