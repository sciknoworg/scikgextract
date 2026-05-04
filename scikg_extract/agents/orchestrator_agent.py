"""
Orchestrator Agent for managing the overall extraction workflow including structured knowledge extraction and LLM-as-a-Judge validation.

The Orchestrator Agent serves as the central controller for the entire structured knowledge extraction workflow. It compiles and manages the execution of the LangGraph StateGraph that defines the sequence of steps for extracting structured knowledge from scientific documents, validating it using LLM-as-a-Judge approaches, and refining it based on feedback. The agent takes in configurations for the extraction process, reflection/validation settings, and feedback mechanisms, and ensures that each component is invoked in the correct order with the appropriate parameters. It also handles routing logic to determine when to invoke the reflection and feedback agents based on workflow settings and evaluation results.
"""
# External imports
from langgraph.graph import StateGraph, START, END
from yescieval.base.rubric import Rubric

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# Scikg_Extract Config Imports
from scikg_extract.config.agents.orchestrator import OrchestratorConfig
from scikg_extract.config.agents.workflow import WorkflowConfig
from scikg_extract.config.process.processConfig import ProcessConfig
from scikg_extract.config.normalization.normalizationConfig import NormalizationConfig
from scikg_extract.config.llm.llmConfig import ProviderRegistry

# SciKG_Extract Callback Imports
from scikg_extract.callbacks.timing_callback import IterationTimingCallback

# Scikg_Extract Agent Imports
from scikg_extract.agents.extraction_agent import extract_knowledge
from scikg_extract.agents.reflection_agent import validate_extracted_processes
from scikg_extract.agents.feedback_agent import provide_feedback
from scikg_extract.agents.states import ExtractionState

def validate_orchestrator_config_params(orchestrator_config: OrchestratorConfig, workflowConfig: WorkflowConfig) -> bool:
    """
    Validates the parameters provided in the OrchestratorConfig.
    Args:
        orchestrator_config (OrchestratorConfig): Configuration for the Orchestrator Agent.
        workflowConfig (WorkflowConfig): Configuration for the overall extraction workflow.
    Returns:
        bool: True if all parameters are valid, otherwise raises ValueError.
    Raises:
        ValueError: If any of the required parameters are missing or invalid.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Validating Orchestrator Agent configuration parameters...")

    # Step 1: Validate LLM models (LLM model for extraction, normalization, reflection and feedback)
    if not ProviderRegistry.has_model_or_provider_from_string(orchestrator_config.extraction_llm):
        raise ValueError(f"Extraction LLM model {orchestrator_config.extraction_llm} not found in registry.")
    logger.debug(f"LLM model for extraction: {orchestrator_config.extraction_llm} is valid.")

    if workflowConfig.normalize_extracted_data:
        if not ProviderRegistry.has_model_or_provider_from_string(orchestrator_config.normalization_llm):
            raise ValueError(f"Normalization LLM model {orchestrator_config.normalization_llm} not found in registry.")
        logger.debug(f"LLM model for normalization: {orchestrator_config.normalization_llm} is valid.")
    
    if workflowConfig.validate_extracted_data:
        reflection_mode = workflowConfig.reflection_mode.lower().strip() if workflowConfig.reflection_mode else "single"
        if reflection_mode in ("multi-judge", "debate"):
            # Multi-judge/debate modes don't require reflection_llm; summarizer_llm is validated in Step 5
            if orchestrator_config.reflection_llm:
                if not ProviderRegistry.has_model_or_provider_from_string(orchestrator_config.reflection_llm):
                    raise ValueError(f"Reflection LLM model {orchestrator_config.reflection_llm} not found in registry.")
                logger.debug(f"LLM model for reflection: {orchestrator_config.reflection_llm} is valid.")
        else:
            # Single mode requires reflection_llm
            if not ProviderRegistry.has_model_or_provider_from_string(orchestrator_config.reflection_llm):
                raise ValueError(f"Reflection LLM model {orchestrator_config.reflection_llm} not found in registry.")
            logger.debug(f"LLM model for reflection: {orchestrator_config.reflection_llm} is valid.")

    if workflowConfig.refine_extracted_data: 
        if not ProviderRegistry.has_model_or_provider_from_string(orchestrator_config.feedback_llm):
            raise ValueError(f"Feedback LLM model {orchestrator_config.feedback_llm} not found in registry.")
        logger.debug(f"LLM model for feedback: {orchestrator_config.feedback_llm} is valid.")

    # Step 2: Check that process schema, scientific document are provided
    if not orchestrator_config.process_schema:
        raise ValueError("Process schema is missing in the Orchestrator configuration.")
    if not orchestrator_config.scientific_document:
        raise ValueError("Scientific document is missing in the Orchestrator configuration.")
    logger.debug("Process schema and scientific document are provided.")
    
    # Step 3: Check if LLM-as-a-Judge rubrics (at least one) are provided if validation is enabled
    if workflowConfig.validate_extracted_data:
        if not orchestrator_config.rubrics:
            raise ValueError("At least one rubric must be provided for LLM-as-a-Judge validation in the Orchestrator configuration.")
        logger.debug("At least one rubric is provided for LLM-as-a-Judge validation.")

    # Step 4: Check if all Rubrics are of type Rubric from yescieval if validation is enabled
    if workflowConfig.validate_extracted_data:
        valid_rubrics = all(issubclass(rubric, Rubric) for rubric in orchestrator_config.rubrics)
        if not valid_rubrics:
            raise ValueError("All provided rubrics must be instances of the Rubric class from yescieval.")
        logger.debug("All provided rubrics are valid instances of the Rubric class.")

    # Step 5: Validate multi-judge and debate mode specific configurations
    reflection_mode = workflowConfig.reflection_mode.lower().strip() if workflowConfig.reflection_mode else "single"
    if workflowConfig.validate_extracted_data and reflection_mode in ("multi-judge", "debate"):
        # Judge models are required for multi-judge and debate modes
        if not orchestrator_config.reflection_judge_llms:
            raise ValueError(f"Reflection judge models must be provided for '{reflection_mode}' reflection mode.")
        logger.debug(f"Reflection judge models are configured for '{reflection_mode}' mode: {orchestrator_config.reflection_judge_llms}")

        # Summarizer LLM is required for multi-judge and debate modes
        if not orchestrator_config.summarizer_llm:
            raise ValueError(f"Summarizer LLM model must be provided for '{reflection_mode}' reflection mode.")
        if not ProviderRegistry.has_model_or_provider_from_string(orchestrator_config.summarizer_llm):
            raise ValueError(f"Summarizer LLM model {orchestrator_config.summarizer_llm} not found in registry.")
        logger.debug(f"Summarizer LLM model: {orchestrator_config.summarizer_llm} is valid.")

        # Critic models are required for debate mode
        if reflection_mode == "debate":
            if not orchestrator_config.reflection_critic_llms:
                raise ValueError("Reflection critic models must be provided for 'debate' reflection mode.")
            logger.debug(f"Reflection critic models are configured for debate mode: {orchestrator_config.reflection_critic_llms}")

    # Return True if all validations pass
    return True

def route_to_reflection_agent(state: ExtractionState) -> str:
    """
    Routes to the Reflection Agent for validation if enabled in the workflow configuration.
    Args:
        state (ExtractionState): The current state of the extraction process.
    Returns:
        str: The name of the next node to route to.
    """
    # Check if rubrics and retries are configured
    if state.rubric_names and state.total_validation_retries >= 0:
        # Single mode requires reflection_llm, Multi-judge/debate modes require summarizer_llm and judge/critic LLMs
        has_single = bool(state.reflection_llm)
        has_multi = bool(state.summarizer_llm and (state.reflection_judge_llms or state.reflection_critic_llms))
        if has_single or has_multi:
            return "validate_extracted_processes"
    
    # Otherwise, terminate the workflow
    return END
    
def route_to_feedback_agent(state: ExtractionState) -> str:
    """
    Routes to the Feedback Agent for providing feedback if evaluation results are available and feedback LLM is specified.
    Args:
        state (ExtractionState): The current state of the extraction process.
    Returns:
        str: The name of the next node to route to.
    """
    # Check if feedback LLM model is specified and evaluation results are available
    if state.feedback_llm and state.evaluation_results  and state.total_validation_retries > 0:
        return "provide_feedback"

    # Otherwise, terminate the workflow
    return END
    
def refine_extracted_knowledge_termination(state: ExtractionState) -> str:
    """
    Determines when to terminate the refinement loop based on the retries left for validation failures.
    Args:
        state (ExtractionState): The current state of the extraction process.
    Returns:
        str: The name of the next node to route to.
    """
    # Check for average evaluation score across all rubrics
    avg_score = sum(float(result["rating"]) for result in state.evaluation_results.values()) / len(state.evaluation_results)
    if avg_score >= 4.0:
        return END

    # Check if there are retries left for refinement
    if state.total_validation_retries > 0:
        return "extract_knowledge"

    # Terminate the refinement loop if no retries left
    return END

def orchestrate_extraction_workflow(orchestrator_config: OrchestratorConfig, workflow_config: WorkflowConfig) -> ExtractionState:
    """
    Orchestrates the overall extraction workflow containing structured knowledge extraction, LLM-as-a-Judge validation and reflection, and finally exporting the final structured knowledge.
    Args:
        orchestrator_config (OrchestratorConfig): Configuration for the Orchestrator Agent.
        workflow_config (WorkflowConfig): Configuration for the overall extraction workflow.
    Returns:
        ExtractionState: The final state containing the extracted and validated structured knowledge.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting Orchestrator Agent for extraction workflow...")

    # Validate the orchestrator configuration parameters upfront
    validate_orchestrator_config_params(orchestrator_config, workflow_config)

    # Create the state graph
    graph = StateGraph(ExtractionState)
    logger.debug("Created StateGraph for the Orchestractor Agent.")

    # Step 1: Initialize the state object for the extraction workflow
    state = {
        "extraction_llm": orchestrator_config.extraction_llm,
        "data_model": orchestrator_config.extraction_data_model,
        "process_name": ProcessConfig.Process_name,
        "process_description": ProcessConfig.Process_description,
        "process_property_constraints": ProcessConfig.Process_property_constraints,
        "process_schema": orchestrator_config.process_schema,
        "process_instances_key": "processes",
        "scientific_document": orchestrator_config.scientific_document,
        "cleaned_extracted_json": workflow_config.clean_extracted_data,
        "normalize_extracted_json": workflow_config.normalize_extracted_data,
        "examples": orchestrator_config.examples,
        "evaluation_results": None,
        "user_feedback_prompt": None
    }
    state = ExtractionState(**state)

    # Step 2: Extract structured knowledge using Extraction Agent
    if workflow_config.normalize_extracted_data:
        state.normalization_llm = orchestrator_config.normalization_llm
        state.pubchem_lmdb_path = orchestrator_config.pubchem_lmdb_path
        state.synonym_to_cid_mapping = orchestrator_config.synonym_to_cid_mapping
        state.normalization_properties_to_include = NormalizationConfig.include_paths
        state.normalization_properties_to_exclude = NormalizationConfig.exclude_paths

    # Add the node for extraction agent
    graph.add_node("extract_knowledge", extract_knowledge)
    logger.debug("Added extract_knowledge node to the graph.")

    # Add the edge from START to extraction agent
    graph.add_edge(START, "extract_knowledge")
    logger.debug("Added edge from START node to extract_knowledge node.")

    # Step 3: Validate the extracted structured knowledge using Reflection Agent and feedback agent if enabled in workflowConfig
    if workflow_config.validate_extracted_data:
        
        # Setup Reflection Config
        state.reflection_mode = workflow_config.reflection_mode
        state.reflection_llm = orchestrator_config.reflection_llm
        state.summarizer_llm = orchestrator_config.summarizer_llm
        state.reflection_judge_llms = orchestrator_config.reflection_judge_llms
        state.reflection_critic_llms = orchestrator_config.reflection_critic_llms
        state.rubric_names = orchestrator_config.rubrics
        state.debate_max_iterations = workflow_config.debate_max_iterations

    # Step 4: Refine the extracted knowledge based on evaluation results using feedback agent if enabled in workflowConfig
    if workflow_config.refine_extracted_data:
        
        # Setup Feedback Config
        state.feedback_llm = orchestrator_config.feedback_llm
        state.total_validation_retries = workflow_config.total_validation_retries

    # Add the node for reflection agent
    graph.add_node("validate_extracted_processes", validate_extracted_processes)
    logger.debug("Added validate_extracted_processes node to the graph.")

    # Add the conditional edge to route to reflection agent if validation is enabled
    graph.add_conditional_edges("extract_knowledge", route_to_reflection_agent)
    logger.debug("Added conditional edges for routing to Reflection Agent based on workflow configuration.")

    # Add the node for feedback agent
    graph.add_node("provide_feedback", provide_feedback)
    logger.debug("Added provide_feedback node to the graph.")

    # Add the conditional edge to route to feedback agent if evaluation results and feedback LLM are available
    graph.add_conditional_edges("validate_extracted_processes", route_to_feedback_agent)
    logger.debug("Added conditional edges for routing to Feedback Agent based on evaluation results and feedback LLM.")

    # Add the refinement loop until termination condition is met
    graph.add_conditional_edges("provide_feedback", refine_extracted_knowledge_termination)
    logger.debug("Added conditional edges for refinement loop based on validation retries left.")
    
    # Compile the graph
    orchestrator_workflow = graph.compile()
    logger.info("Compiled the orchestractor workflow graph.")

    # Add timing callback to track time taken for each iteration of the workflow
    timing_callback = IterationTimingCallback()

    # Set recursion_limit high enough to accommodate all iterations:
    # Each iteration uses ~4 steps (extract → reflect → feedback → route), so
    # (retries + 1) * 10 gives a safe upper bound with room to spare.
    recursion_limit = (workflow_config.total_validation_retries + 1) * 10 + 25

    # Execute the feedback workflow
    logger.info("Invoking the orchestrator workflow...")
    final_state = orchestrator_workflow.invoke(state, config={"callbacks": [timing_callback], "recursion_limit": recursion_limit})

    # Log the iteration durations for each iteration of the workflow
    timing_callback.log_summary()

    # Step 5: Return the final extracted and validated structured knowledge
    return final_state