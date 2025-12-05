from scikg_extract.config.llm.llmConfig import LLM_REGISTRY
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.agents.states import ExtractionState
from scikg_extract.evaluation.rubrics.informativeness import Correctness
from scikg_extract.evaluation.rubrics.informativeness import Completeness

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
        scientific_article=state["scientific_document"],
        process_schema=state["process_schema"],
        extracted_data=state["extracted_json"]
    )

    # Initialize the Judge based on the LLM model
    judge_adapter = LLM_REGISTRY.get(state["validation_llm_model"]).evaluation_judge
    judge = judge_adapter(model=state["validation_llm_model"], data_model=EvaluationRating)

    # Evaluate correctness
    correctness_result = judge.evaluate(correctness_rubric)

    # Update the state with the correctness evaluation results
    if not state["evaluation_results"]: state["evaluation_results"] = {}
    if "evaluation_results" not in state: state["evaluation_results"] = {}
    state["evaluation_results"].update({
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
        scientific_article=state["scientific_document"],
        process_schema=state["process_schema"],
        extracted_data=state["extracted_json"]
    )

    # Initialize the Judge based on the LLM model
    judge_adapter = LLM_REGISTRY.get(state["validation_llm_model"]).evaluation_judge
    judge = judge_adapter(model=state["validation_llm_model"], data_model=EvaluationRating)

    # Evaluate completeness
    completeness_result = judge.evaluate(completness_rubric)
    
    # Update the state with the completeness evaluation results
    if not state["evaluation_results"]: state["evaluation_results"] = {}
    if "evaluation_results" not in state: state["evaluation_results"] = {}
    state["evaluation_results"].update({
        "completeness": completeness_result.model_dump()
    })

    # Return the updated state with evaluation results
    return state