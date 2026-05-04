"""
Summarize Evaluations Tool for consolidating multiple individual evaluations into a single authoritative evaluation per rubric using a dedicated summarizer LLM.

Used in both multi-judge and debate reflection modes. The summarizer LLM reads all individual evaluations for a rubric and produces a consolidated rating and rationale in the same EvaluationRating format, ensuring compatibility with the downstream feedback pipeline.
"""

# Python Imports
import json
from types import SimpleNamespace

# SciKGExtract Imports
from scikg_extract.config.llm.llmConfig import ProviderRegistry
from scikg_extract.config.process.processConfig import ProcessConfig
from scikg_extract.config.evaluation.rubricConfig import get_rubric_config
from scikg_extract.prompts.evaluation import summarize_evaluations as summarize_prompts
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.agents.states import ExtractionState

# Data Models
from data.models.evaluation.evaluation_rating import EvaluationRating


# Rubric descriptions used by the summarizer to understand what each rubric measures
RUBRIC_DESCRIPTIONS = {
    "Correctness": "Measures how accurately the extracted structured data represents the processes described in the scientific article while adhering to the process schema.",
    "Completeness": "Measures how fully the extracted structured data captures all processes and required information described in the article.",
}

def summarize_rubric_evaluations(rubric_name: str):
    """
    Factory function that creates a summarization node for a given rubric. It consolidates individual evaluations (from multi-judge or debate rounds) into a single authoritative evaluation using the summarizer LLM.
    Args:
        rubric_name (str): The name of the rubric to summarize (e.g., "Correctness", "Completeness").
    Returns:
        callable: A function that takes ExtractionState and returns the updated state with consolidated evaluation_results for this rubric.
    """

    def _summarize(state: ExtractionState) -> ExtractionState:
        """
        Consolidates individual evaluations for a given rubric into a single authoritative evaluation using the summarizer LLM.
        Args:
            state (ExtractionState): The current state of the extraction process containing necessary data and individual evaluations for this rubric.
        Returns:
            ExtractionState: The updated state with consolidated evaluation_results for this rubric stored in state.evaluation_results.
        """

        # Initialize the logger
        logger = LogHandler.get_logger(__name__)
        logger.info(f"Starting evaluation summarization for rubric: {rubric_name}")

        # Get individual evaluations for this rubric
        rubric_key = rubric_name.lower()
        matching_entries = [eval["evaluations"] for eval in state.individual_evaluation_results if eval["rubric"].lower() == rubric_key]

        if not matching_entries:
            logger.warning(f"No individual evaluations found for {rubric_name}. Skipping summarization.")
            return state

        # Unwrap: matching_entries is [[eval1, eval2, ...]], we need the inner list
        individual_evals = matching_entries[0]

        # If only one evaluation, use it directly without summarization
        if len(individual_evals) == 1:
            logger.info(f"Only one evaluation for {rubric_name}. Using it directly as the consolidated result.")
            if not state.evaluation_results:
                state.evaluation_results = {}
            state.evaluation_results[rubric_key] = {
                "rating": individual_evals[0]["rating"],
                "rationale": individual_evals[0]["rationale"]
            }
            return state

        # Resolve the summarizer LLM
        summarizer_model = state.summarizer_llm
        if not summarizer_model:
            # Fallback to the validation LLM if no summarizer is configured
            summarizer_model = state.reflection_llm
            logger.warning("No summarizer LLM configured. Falling back to validation LLM.")

        logger.info(f"Using summarizer LLM: {summarizer_model}")

        # Resolve the adapter for the summarizer
        llm_config = ProviderRegistry.resolve_from_string(summarizer_model)

        # Format individual evaluations as a readable string for the prompt
        formatted_evals = _format_individual_evaluations(individual_evals)

        # Get rubric description
        rubric_description = RUBRIC_DESCRIPTIONS.get(rubric_name, rubric_name)

        # Build the prompt variables
        var_dict = {
            "process_name": ProcessConfig.Process_name,
            "process_description": ProcessConfig.Process_description,
            "rubric_name": rubric_name,
            "rubric_description": rubric_description,
            "scientific_article": state.scientific_document,
            "process_schema": json.dumps(state.process_schema, indent=2),
            "extracted_data": json.dumps(state.extracted_json, indent=2),
            "individual_evaluations": formatted_evals
        }

        # Build the prompt template
        prompt_template = SimpleNamespace(
            system_prompt=summarize_prompts.system_prompt,
            user_prompt=summarize_prompts.user_prompt
        )

        # Initialize the adapter and make a structured completion call
        adapter = llm_config.inference_adapter(model_name=llm_config.model_name, temperature=0.1)
        consolidated_result = adapter.structured_completion(prompt_template, var_dict, EvaluationRating)

        if consolidated_result:
            if not state.evaluation_results:
                state.evaluation_results = {}
            state.evaluation_results[rubric_key] = consolidated_result.model_dump()
            logger.info(f"Summarized {rubric_name}: rating={consolidated_result.rating}")
        else:
            logger.error(f"Summarizer returned None for {rubric_name}. Using highest-rated individual evaluation as fallback.")
            # Fallback: use the evaluation with the highest rating
            if not state.evaluation_results:
                state.evaluation_results = {}
            best_eval = max(individual_evals, key=lambda e: int(e.get("rating", "0")))
            state.evaluation_results[rubric_key] = {
                "rating": best_eval["rating"],
                "rationale": best_eval["rationale"]
            }

        # Return the updated state with the consolidated evaluation result for this rubric
        return state

    # Set a descriptive name for the function (used as node name in LangGraph)
    _summarize.__name__ = f"summarize_{rubric_name.lower()}_evaluations"
    
    # Return the summarization function to be used as a node action in the graph
    return _summarize


def _format_individual_evaluations(evaluations: list[dict]) -> str:
    """
    Formats a list of individual evaluations into a readable string for the summarizer prompt.
    Args:
        evaluations (list[dict]): List of evaluation dicts with 'rating', 'rationale', and optionally 'judge'.
    Returns:
        str: Formatted string representation of all evaluations.
    """
    lines = []
    for idx, evaluation in enumerate(evaluations):
        judge_id = evaluation.get("judge", f"Judge {idx + 1}")
        rating = evaluation.get("rating", "N/A")
        rationale = evaluation.get("rationale", "No rationale provided.")
        lines.append(f"--- Evaluation {idx + 1} ({judge_id}) ---")
        lines.append(f"Rating: {rating}")
        lines.append(f"Rationale: {rationale}")
        lines.append("")
    return "\n".join(lines)