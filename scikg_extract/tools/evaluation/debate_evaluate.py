"""
Debate Evaluation Tool for evaluating extracted structured knowledge through evaluator-critic debate rounds.

Each evaluator-critic pair engages in a structured debate for a given rubric. The evaluator produces an initial evaluation, then the critic critiques it. If the critic is not satisfied, the evaluator revises their assessment. This loop continues until the critic is satisfied or the maximum number of debate iterations is reached. The final evaluation from each pair is collected for downstream summarization.
"""

# Python Imports
import json
from types import SimpleNamespace

# SciKGExtract Imports
from scikg_extract.config.llm.llmConfig import ProviderRegistry
from scikg_extract.config.evaluation.rubricConfig import get_rubric_config
from scikg_extract.config.process.processConfig import ProcessConfig
from scikg_extract.prompts.evaluation import debate_critic as critic_prompts
from scikg_extract.prompts.evaluation import debate_evaluator as evaluator_revision_prompts
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.agents.states import ExtractionState

# Data Models
from data.models.evaluation.evaluation_rating import EvaluationRating
from data.models.evaluation.critic_response import CriticResponse

# Rubric descriptions for prompt formatting
RUBRIC_DESCRIPTIONS = {
    "Correctness": "Measures how accurately the extracted structured data represents the processes described in the scientific article while adhering to the process schema.",
    "Completeness": "Measures how fully the extracted structured data captures all processes and required information described in the article.",
}

def debate_evaluate_rubric(rubric_name: str):
    """
    Factory function that creates a debate evaluation node for a given rubric. Each configured evaluator-critic pair debates the rubric through multiple rounds. The final evaluation from each pair is stored in state.individual_evaluation_results for downstream summarization.
    Args:
        rubric_name (str): The name of the rubric to evaluate (e.g., "Correctness", "Completeness").
    Returns:
        callable: A function that takes ExtractionState and returns the updated state with debate evaluation results from all evaluator-critic pairs for this rubric.
    """

    def _debate(state: ExtractionState) -> ExtractionState:
        """
        Runs the debate evaluation for a given rubric across all evaluator-critic pairs.
        Args:
            state (ExtractionState): The current state of the extraction process containing extracted data, judge/critic configurations, and debate settings.
        Returns:
            ExtractionState: The updated state with debate evaluation results for this rubric stored in state.individual_evaluation_results.
        """

        # Initialize the logger
        logger = LogHandler.get_logger(__name__)
        logger.info(f"Starting debate evaluation for rubric: {rubric_name}")

        # Get the rubric class from the registry for the initial evaluation
        rubric_config = get_rubric_config(rubric_name)
        rubric_class = rubric_config.rubric_class

        # Determine the extracted data to evaluate (prefer normalized if available)
        extracted_data = state.extracted_json if not state.normalized_json else state.normalized_json

        # Instantiate the rubric with current state data
        rubric_instance = rubric_class(
            scientific_article=state.scientific_document,
            process_schema=state.process_schema,
            extracted_data=extracted_data
        )

        # Determine evaluator-critic pairs
        judge_llms = state.reflection_judge_llms
        if not judge_llms:
            judge_llms = [state.reflection_llm]
            logger.warning("No reflection judge models configured. Falling back to single reflection LLM.")

        critic_llms = state.reflection_critic_llms
        if not critic_llms:
            critic_llms = judge_llms
            logger.warning("No reflection critic models configured. Using evaluator models as critics.")

        # Pair evaluators with critics (cycle critics if fewer than evaluators)
        pairs = _pair_evaluators_with_critics(judge_llms, critic_llms)
        max_iterations = state.debate_max_iterations

        # Run debate for each evaluator-critic pair
        debate_results = []
        for pair_idx, (eval_llm_str, critic_llm_str) in enumerate(pairs):
            eval_model, eval_provider = ProviderRegistry.parse_llm_string(eval_llm_str)
            critic_model, critic_provider = ProviderRegistry.parse_llm_string(critic_llm_str)
            logger.info(f"Debate pair {pair_idx + 1}/{len(pairs)}: Evaluator={eval_llm_str}, Critic={critic_llm_str}")

            # Step 1: Initial evaluation using the standard judge pattern
            logger.info(f"Pair {pair_idx + 1} - Initial evaluation by {eval_provider}:{eval_model}...")
            eval_llm_config = ProviderRegistry.resolve(eval_model, eval_provider)
            judge = eval_llm_config.evaluation_judge(model=eval_model, data_model=EvaluationRating)
            initial_result = judge.evaluate(rubric_instance)
            if not initial_result:
                logger.warning(f"Pair {pair_idx + 1} - Evaluator returned None. Skipping this pair.")
                continue

            current_rating = initial_result.rating
            current_rationale = initial_result.rationale
            logger.debug(f"Pair {pair_idx + 1} - Initial evaluation: rating={current_rating}")

            # Step 2: Debate loop — critic critiques, evaluator revises
            rubric_description = RUBRIC_DESCRIPTIONS.get(rubric_name, rubric_name)

            for debate_round in range(1, max_iterations + 1):
                logger.info(f"Pair {pair_idx + 1} - Debate round {debate_round}/{max_iterations}")

                # Critic critiques the current evaluation
                critic_response = _critic_evaluate(
                    state=state,
                    rubric_name=rubric_name,
                    rubric_description=rubric_description,
                    critic_model=critic_model,
                    critic_provider=critic_provider,
                    evaluator_rating=current_rating,
                    evaluator_rationale=current_rationale,
                    extracted_data=extracted_data,
                    logger=logger
                )

                if not critic_response:
                    logger.warning(f"Pair {pair_idx + 1} - Critic returned None in round {debate_round}. Keeping current evaluation.")
                    break

                logger.debug(f"Pair {pair_idx + 1} - Critic satisfied: {critic_response.satisfied}, suggested_rating: {critic_response.suggested_rating}")

                # If critic is satisfied, the evaluation is final
                if critic_response.satisfied:
                    logger.info(f"Pair {pair_idx + 1} - Critic satisfied in round {debate_round}. Debate concluded.")
                    break

                # Evaluator revises based on critic feedback
                revised_result = _evaluator_revise(
                    state=state,
                    rubric_name=rubric_name,
                    rubric_description=rubric_description,
                    eval_model=eval_model,
                    eval_provider=eval_provider,
                    previous_rating=current_rating,
                    previous_rationale=current_rationale,
                    critic_response=critic_response,
                    extracted_data=extracted_data,
                    logger=logger
                )

                if not revised_result:
                    logger.warning(f"Pair {pair_idx + 1} - Evaluator revision returned None in round {debate_round}. Keeping previous evaluation.")
                    break

                current_rating = revised_result.rating
                current_rationale = revised_result.rationale
                logger.debug(f"Pair {pair_idx + 1} - Revised evaluation: rating={current_rating}")

            # Collect the final evaluation for this pair
            final_evaluation = {
                "rating": current_rating,
                "rationale": current_rationale,
                "judge": eval_llm_str,
                "critic": critic_llm_str
            }
            debate_results.append(final_evaluation)
            logger.info(f"Pair {pair_idx + 1} - Final evaluation: rating={current_rating}")

        # Store individual evaluations in state
        if not state.individual_evaluation_results:
            state.individual_evaluation_results = []

        state.individual_evaluation_results.append({
            "rubric": rubric_name,
            "evaluations": debate_results
        })

        logger.info(f"Debate evaluation for {rubric_name} complete. {len(debate_results)} pairs contributed.")

        # Return the updated state with debate evaluation results for this rubric
        return state

    # Set a descriptive name for the function (used as node name in LangGraph)
    _debate.__name__ = f"debate_evaluate_{rubric_name.lower()}"

    # Return the debate evaluation function to be used as a node action in the graph
    return _debate

def _critic_evaluate(state: ExtractionState, rubric_name: str, rubric_description: str, critic_model: str, critic_provider: str, evaluator_rating: str, evaluator_rationale: str, extracted_data: dict, logger) -> CriticResponse | None:
    """
    Runs the critic's evaluation of the current evaluator assessment.
    Args:
        state (ExtractionState): The current extraction state with scientific document and schema.
        rubric_name (str): The name of the rubric being evaluated.
        rubric_description (str): Description of the rubric for prompt formatting.
        critic_model (str): The critic LLM model name.
        critic_provider (str): The critic LLM provider name.
        evaluator_rating (str): The evaluator's current rating.
        evaluator_rationale (str): The evaluator's current rationale.
        extracted_data (dict): The extracted data being evaluated.
        logger: Logger instance for debug output.
    Returns:
        CriticResponse | None: The critic's response or None if the call fails.
    """

    # Resolve the critic adapter
    llm_config = ProviderRegistry.resolve(critic_model, critic_provider)
    adapter = llm_config.inference_adapter(model_name=critic_model, temperature=0.1)

    # Build prompt variables
    var_dict = {
        "process_name": ProcessConfig.Process_name,
        "process_description": ProcessConfig.Process_description,
        "rubric_name": rubric_name,
        "rubric_description": rubric_description,
        "scientific_article": state.scientific_document,
        "process_schema": json.dumps(state.process_schema, indent=2),
        "extracted_data": json.dumps(extracted_data, indent=2),
        "evaluator_rating": evaluator_rating,
        "evaluator_rationale": evaluator_rationale,
    }

    # Build prompt template
    prompt_template = SimpleNamespace(
        system_prompt=critic_prompts.system_prompt,
        user_prompt=critic_prompts.user_prompt
    )

    # Call the critic LLM with structured output
    result = adapter.structured_completion(prompt_template, var_dict, CriticResponse)
    return result

def _evaluator_revise(state: ExtractionState, rubric_name: str, rubric_description: str, eval_model: str, eval_provider: str, previous_rating: str, previous_rationale: str, critic_response: CriticResponse, extracted_data: dict, logger) -> EvaluationRating | None:
    """
    Runs the evaluator's revision in response to critic feedback.
    Args:
        state (ExtractionState): The current extraction state with scientific document and schema.
        rubric_name (str): The name of the rubric being evaluated.
        rubric_description (str): Description of the rubric for prompt formatting.
        eval_model (str): The evaluator LLM model name.
        eval_provider (str): The evaluator LLM provider name.
        previous_rating (str): The evaluator's previous rating.
        previous_rationale (str): The evaluator's previous rationale.
        critic_response (CriticResponse): The critic's response containing critique and suggested rating.
        extracted_data (dict): The extracted data being evaluated.
        logger: Logger instance for debug output.
    Returns:
        EvaluationRating | None: The revised evaluation or None if the call fails.
    """

    # Resolve the evaluator adapter
    llm_config = ProviderRegistry.resolve(eval_model, eval_provider)
    adapter = llm_config.inference_adapter(model_name=eval_model, temperature=0.1)

    # Build prompt variables
    var_dict = {
        "process_name": ProcessConfig.Process_name,
        "process_description": ProcessConfig.Process_description,
        "rubric_name": rubric_name,
        "rubric_description": rubric_description,
        "scientific_article": state.scientific_document,
        "process_schema": json.dumps(state.process_schema, indent=2),
        "extracted_data": json.dumps(extracted_data, indent=2),
        "previous_rating": previous_rating,
        "previous_rationale": previous_rationale,
        "critic_satisfied": str(critic_response.satisfied),
        "critic_critique": critic_response.critique,
        "critic_suggested_rating": critic_response.suggested_rating or "N/A",
    }

    # Build prompt template
    prompt_template = SimpleNamespace(
        system_prompt=evaluator_revision_prompts.system_prompt,
        user_prompt=evaluator_revision_prompts.user_prompt
    )

    # Call the evaluator LLM with structured output
    result = adapter.structured_completion(prompt_template, var_dict, EvaluationRating)
    return result

def _pair_evaluators_with_critics(judge_llms: list[str], critic_llms: list[str]) -> list[tuple[str, str]]:
    """
    Pairs each evaluator with a critic. If there are fewer critics than evaluators, critics are cycled.
    Args:
        judge_llms (list[str]): List of evaluator LLM strings (e.g., "OPENAI:gpt-4o").
        critic_llms (list[str]): List of critic LLM strings.
    Returns:
        list[tuple[str, str]]: List of (evaluator_llm, critic_llm) pairs.
    """
    pairs = []
    for idx, judge in enumerate(judge_llms):
        critic = critic_llms[idx % len(critic_llms)]
        pairs.append((judge, critic))
    return pairs