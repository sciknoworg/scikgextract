"""
Prompt with Feedback Tool for SciKGExtract.

This tool generates a user prompt that incorporates feedback on the extracted structured knowledge to guide further refinement. It retrieves raw feedback from the state, uses an LLM to format it into readable text, and programmatically combines it with the original extraction user prompt. The updated prompt is then stored back in the state for use in the next iteration of the extraction process.
"""
# SciKGExtract Config Imports
from scikg_extract.config.llm.llmConfig import ProviderRegistry

# SciKGExtract Utils Imports
from scikg_extract.utils.log_handler import LogHandler

# SciKGExtract State Imports
from scikg_extract.agents.states import ExtractionState

# SciKGExtract Prompt Imports
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
    llm_config = ProviderRegistry.resolve_from_string(state.feedback_llm)
    model_adapter = llm_config.inference_adapter(model_name=llm_config.model_name, temperature=0.1, response_format="text")
    logger.debug(f"Initialized Model adapter for feedback: {model_adapter}")

    # Retrieve the raw feedbacks from the state
    feedbacks = state.evaluation_results

    # Format the variables for the prompt
    var_dict = {"process_name": state.process_name, "process_description": state.process_description, "raw_feedbacks": feedbacks}

    # Use the LLM to format and structure the raw feedbacks into readable text
    formatted_feedback = model_adapter.completion(format_feedback, var_dict)
    logger.debug(f"Generated formatted feedback:\n{formatted_feedback}\n")
    logger.info("Raw feedback formatted successfully.")

    # Escape literal curly braces in the LLM-generated feedback
    escaped_feedback = formatted_feedback.replace("{", "{{").replace("}", "}}")

    # Programmatically combine the original extraction user prompt with the escaped feedback
    combined_prompt = (
        structure_knowledge_extraction.user_prompt
        + "\n\nEvaluation Feedback from Reflection Agent:\n"
        + "Use the following feedback to improve and refine the extraction. Address each issue mentioned below:\n\n"
        + escaped_feedback
    )
    logger.debug(f"Combined user prompt with feedback:\n{combined_prompt}\n")

    # Update the state with the combined user prompt
    state.user_feedback_prompt = combined_prompt

    # Return the updated state with the user feedback prompt
    return state