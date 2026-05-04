"""
Multi-Judge Evaluation Tool for evaluating extracted structured knowledge using multiple LLM judges.

Each judge independently evaluates the extraction using the same rubric (e.g., Correctness or Completeness). The individual evaluations are collected and stored in the state for downstream summarization.
"""

# SciKGExtract Imports
from scikg_extract.config.llm.llmConfig import ProviderRegistry
from scikg_extract.config.evaluation.rubricConfig import get_rubric_config
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.agents.states import ExtractionState

# Data Models
from data.models.evaluation.evaluation_rating import EvaluationRating


def multi_judge_evaluate_rubric(rubric_name: str):
    """
    Factory function that creates a multi-judge evaluation node for a given rubric. Each configured judge evaluates the rubric independently, and all results are stored in state.individual_evaluation_results.
    Args:
        rubric_name (str): The name of the rubric to evaluate (e.g., "Correctness", "Completeness").
    Returns:
        callable: A function that takes ExtractionState and returns the updated state with individual evaluation results from all judges for this rubric.
    """

    def _evaluate(state: ExtractionState) -> ExtractionState:
        """
        Evaluates the extracted structured knowledge using multiple LLM judges based on the specified rubric.
        Args:
            state (ExtractionState): The current state of the extraction process containing necessary data and judge configurations.
        Returns:
            ExtractionState: The updated state with individual evaluation results from all judges for this rubric stored in state.individual_evaluation_results.
        """
        
        # Initialize the logger
        logger = LogHandler.get_logger(__name__)
        logger.info(f"Starting multi-judge evaluation for rubric: {rubric_name}")

        # Get the rubric class from the registry
        rubric_config = get_rubric_config(rubric_name)
        rubric_class = rubric_config.rubric_class

        # Instantiate the rubric with current state data
        rubric_instance = rubric_class(
            scientific_article=state.scientific_document,
            process_schema=state.process_schema,
            extracted_data=state.extracted_json if not state.normalized_json else state.normalized_json
        )

        # Determine which judge models to use
        judge_llms = state.reflection_judge_llms
        if not judge_llms:
            # Fallback to the single reflection LLM if no judge models are configured
            judge_llms = [state.reflection_llm]
            logger.warning("No reflection judge models configured. Falling back to single reflection LLM.")

        # Collect individual evaluations from each judge
        judge_evaluations = []
        for idx, judge_llm in enumerate(judge_llms):
            model_name, provider_name = ProviderRegistry.parse_llm_string(judge_llm)
            logger.info(f"Judge {idx + 1}/{len(judge_llms)}: {judge_llm} evaluating {rubric_name}...")

            # Resolve the judge adapter for this provider/model
            llm_config = ProviderRegistry.resolve(model_name, provider_name)
            judge = llm_config.evaluation_judge(model=model_name, data_model=EvaluationRating)

            # Evaluate the rubric
            result = judge.evaluate(rubric_instance)
            if result:
                evaluation = result.model_dump()
                evaluation["judge"] = judge_llm
                judge_evaluations.append(evaluation)
                logger.debug(f"Judge {idx + 1} ({judge_llm}) result: rating={evaluation['rating']}")
            else:
                logger.warning(f"Judge {idx + 1} ({judge_llm}) returned None for {rubric_name}.")

        # Store individual evaluations in state keyed by rubric name. individual_evaluation_results is a list of evaluations for each judge for this rubric
        if not state.individual_evaluation_results:
            state.individual_evaluation_results = []
        
        # Append the evaluations for this rubric to the list of individual evaluation results in the state
        state.individual_evaluation_results.append({
            "rubric": rubric_name,
            "evaluations": judge_evaluations
        })

        logger.info(f"Multi-judge evaluation for {rubric_name} complete. {len(judge_evaluations)} judges contributed.")
        
        # Return the updated state with individual evaluation results for this rubric
        return state

    # Set a descriptive name for the function (used as node name in LangGraph)
    _evaluate.__name__ = f"multi_judge_evaluate_{rubric_name.lower()}"
    
    # Return the evaluation function to be used as a node action in the graph
    return _evaluate