from scikg_extract.config.llm.llmConfig import LLM_REGISTRY
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.agents.states import ExtractionState
from scikg_extract.prompts.tools import format_feedback
from scikg_extract.prompts.tools import structure_knowledge_extraction

def prompt_with_feedback(state: ExtractionState) -> ExtractionState:
    """
    Generates a user prompt that includes feedback on the extracted structured knowledge to guide further refinement.
    Args:
        state (ExtractionState): The current state of the extraction process containing necessary data.
    Returns:
        ExtractionState: The updated state with the generated user prompt.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting updating prompt with evaluation feedback...")

    # Initialize the LLM model for feedback generation
    inference_adapter = LLM_REGISTRY.get(state["feedback_llm_model"]).inference_adapter
    model_adapter = inference_adapter(model_name=state["feedback_llm_model"], temperature=0.1, response_format="text")
    logger.debug(f"Initialized Model adapter for feedback: {model_adapter}")

    # Retrieve and format the feedbacks from the state
    feedbacks = state["evaluation_results"]

    # Format the variables for the prompt
    var_dict = {"process_name": state["process_name"], "process_description": state["process_description"], "original_user_prompt": structure_knowledge_extraction.user_prompt, "raw_feedbacks": feedbacks}

    # Format and structure the user prompt for refined extraction
    formatted_prompt = model_adapter.completion(format_feedback, var_dict)
    logger.debug(f"Generated formatted prompt with feedback: {formatted_prompt}")
    logger.info("Prompt updated with feedback successfully.")

    # Update the state with the new user prompt
    state["user_feedback_prompt"] = formatted_prompt

    # Return the updated state with the user feedback prompt
    return state