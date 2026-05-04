"""
Evaluation tools for SciKGExtract.

Defines functions that can be used as tools by the Orchestrator Agent to evaluate the extracted structured knowledge. These tools utilize LLMs as judges to assess the correctness and completeness of the extracted data based on the scientific document and process schema. The evaluation results are stored in the agent's state for later aggregation and analysis.
"""
# SciKGExtract Config Imports
from scikg_extract.config.llm.llmConfig import ProviderRegistry

# SciKGExtract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# SciKGExtract Agent State Imports
from scikg_extract.agents.states import ExtractionState

# SciKGExtract Evaluation Imports
from scikg_extract.evaluation.rubrics.informativeness import Correctness
from scikg_extract.evaluation.rubrics.informativeness import Completeness

# Data model for Evaluation Ratings
from data.models.evaluation.evaluation_rating import EvaluationRating

def evaluate_extraction_correctness(state: ExtractionState) -> ExtractionState:
    """
    Evaluates the correctness of the extracted structured knowledge using an LLM-as-a-judge approach.
    Args:
        state (ExtractionState): The current state of the extraction process containing necessary data.
    Returns:
        ExtractionState: The updated state with the evaluation results.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting extraction evaluation tool (correctness)...")

    # Initialize the Correctness rubric
    correctness_rubric = Correctness(
        scientific_article=state.scientific_document,
        process_schema=state.process_schema,
        extracted_data=state.extracted_json if not state.normalized_json else state.normalized_json
    )

    # Initialize the Judge based on the LLM model
    llm_config = ProviderRegistry.resolve_from_string(state.reflection_llm)
    judge = llm_config.evaluation_judge(model=llm_config.model_name, data_model=EvaluationRating)

    # Evaluate correctness
    correctness_result = judge.evaluate(correctness_rubric)
    logger.debug(f"Correctness evaluation result: {correctness_result}")

    if not correctness_result:
        logger.warning("Correctness evaluation returned None. Skipping update to evaluation results.")
        return state

    # Update the state with the correctness evaluation results
    if not state.evaluation_results: state.evaluation_results = {}
    # if "evaluation_results" not in state: state.evaluation_results = {}
    state.evaluation_results.update({
        "correctness": correctness_result.model_dump()
    })

    # Return the updated state with evaluation results
    return state

def evaluate_extraction_completeness(state: ExtractionState) -> ExtractionState:
    """
    Evaluates the completeness of the extracted structured knowledge using an LLM-as-a-judge approach.
    Args:
        state (ExtractionState): The current state of the extraction process containing necessary data.
    Returns:
        ExtractionState: The updated state with the evaluation results.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting extraction evaluation tool (completeness)...")

    # Initialize the Completeness rubric
    completness_rubric = Completeness(
        scientific_article=state.scientific_document,
        process_schema=state.process_schema,
        extracted_data=state.extracted_json if not state.normalized_json else state.normalized_json
    )

    # Initialize the Judge based on the LLM model
    llm_config = ProviderRegistry.resolve_from_string(state.reflection_llm)
    judge = llm_config.evaluation_judge(model=llm_config.model_name, data_model=EvaluationRating)

    # Evaluate completeness
    completeness_result = judge.evaluate(completness_rubric)
    logger.debug(f"Completeness evaluation result: {completeness_result}")

    if not completeness_result:
        logger.warning("Completeness evaluation returned None. Skipping update to evaluation results.")
        return state
    
    # Update the state with the completeness evaluation results
    if not state.evaluation_results: state.evaluation_results = {}
    # if "evaluation_results" not in state: state.evaluation_results = {}
    state.evaluation_results.update({
        "completeness": completeness_result.model_dump()
    })

    # Return the updated state with evaluation results
    return state