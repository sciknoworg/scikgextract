"""
Script to extract structured biomedical entity and relation information from BioRED dataset abstracts with debate-style multi-judge refinement.
"""
# Python imports
import os
import argparse

# SciKGExtract utility imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import read_json_file, read_text_file, save_json_file

# SciKGExtract agent imports
from scikg_extract.agents.orchestrator_agent import orchestrate_extraction_workflow

# SciKGExtract config imports
from scikg_extract.config.process.processConfig import ProcessConfig
from scikg_extract.config.agents.orchestrator import OrchestratorConfig
from scikg_extract.config.agents.workflow import WorkflowConfig
from scikg_extract.config.llm.llmConfig import ProviderRegistry

# SciKGExtract evaluation imports
from scikg_extract.evaluation.rubrics.informativeness import Completeness, Correctness

# Data model for BioRED
from data.models.schema.biored_schema import BioREDSchema

if __name__ == "__main__":
    """Main function to extract biomedical entity and relation information from BioRED abstracts with debate refinement."""

    # Argument Parser Setup
    parser = argparse.ArgumentParser(description="Extract structured biomedical relation information from BioRED dataset with debate refinement.")
    parser.add_argument("--extraction_llm", type=str, help="The LLM to use for extraction in format 'PROVIDER:model_name' (e.g., 'OPENAI:gpt-4o').")
    parser.add_argument("--reflection_judge_llms", type=str, help="Comma-separated LLMs to use as judges (e.g., 'OPENAI:gpt-5,SAIA:deepseek/deepseek-r1-0528').")
    parser.add_argument("--reflection_critic_llms", type=str, help="Comma-separated LLMs to use as critics (e.g., 'SAIA:qwen/qwen3-30b-a3b-thinking-2507').")
    parser.add_argument("--summarizer_llm", type=str, help="The LLM to use for summarization in format 'PROVIDER:model_name'.")
    parser.add_argument("--feedback_llm", type=str, help="The LLM to use for feedback in format 'PROVIDER:model_name'.")
    parser.add_argument("--results_dir", type=str, help="Directory to save the extracted data.")
    parser.add_argument("--process_schema", type=str, help="Path to the process schema JSON file.")
    parser.add_argument("--process_examples", type=str, help="Path to the gold-standard examples text file.")
    parser.add_argument("--data_split", type=str, default="test", help="Data split to process: train, val, or test (default: test).")

    # Parse the arguments
    args = parser.parse_args()

    # Initialize the LLMs
    extraction_llm = args.extraction_llm if args.extraction_llm else "OPENAI:gpt-4o"
    reflection_judge_llms = args.reflection_judge_llms if args.reflection_judge_llms else "OPENAI:gpt-5,SAIA:deepseek/deepseek-r1-0528"
    reflection_critic_llms = args.reflection_critic_llms if args.reflection_critic_llms else "SAIA:qwen/qwen3-30b-a3b-thinking-2507,SAIA:qwen/qwen3-30b-a3b-thinking-2507"
    summarizer_llm = args.summarizer_llm if args.summarizer_llm else "SAIA:mistralai/ministral-3b-2512"
    feedback_llm = args.feedback_llm if args.feedback_llm else "SAIA:mistralai/ministral-3b-2512"

    # Build unique run identifier for concurrent execution (LLM name + PID)
    run_id = f"{extraction_llm}_{os.getpid()}"

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("scikg_extract", run_id=run_id)
    logger.info("Starting BioRED information extraction script with debate-style multi-judge refinement...")
    logger.info(f"Using extraction LLM: {extraction_llm}")
    logger.info(f"Using reflection judge LLMs: {reflection_judge_llms}")
    logger.info(f"Using reflection critic LLMs: {reflection_critic_llms}")
    logger.info(f"Using summarizer LLM: {summarizer_llm}")
    logger.info(f"Using feedback LLM: {feedback_llm}")

    # Override ProcessConfig for BioRED
    ProcessConfig.Process_name = "Biomedical Relation Extraction"
    ProcessConfig.Process_description = """
    The BioRED (Biomedical Relation Extraction Dataset) task involves extracting multiple types of biomedical named entities and their pairwise relations from PubMed abstracts. The dataset covers six entity types: GeneOrGeneProduct, DiseaseOrPhenotypicFeature, ChemicalEntity, SequenceVariant, OrganismTaxon, and CellLine. Relations span eight types including Association, Positive Correlation, Negative Correlation, Binding, Conversion, Cotreatment, Drug Interaction, and Comparison. Each relation also has a novelty flag indicating whether it represents a novel finding reported in the abstract.
    """
    ProcessConfig.Process_property_constraints = """
    1. Entity types: Extract entities of exactly these 6 types: GeneOrGeneProduct, DiseaseOrPhenotypicFeature,
       ChemicalEntity, SequenceVariant, OrganismTaxon, CellLine.
    2. Identifiers: Each entity should have an appropriate database identifier (e.g., NCBI Gene ID, MeSH ID,
       NCBI Taxonomy ID, CL ontology ID).
    3. Offsets: Include character offset and length for each entity mention in the text.
    4. Relation types: Extract relations of these 8 types: Association, Positive_Correlation,
       Negative_Correlation, Binding, Conversion, Cotreatment, Drug_Interaction, Comparison.
    5. Novelty: Each relation must include a boolean 'novel' flag indicating whether the finding is novel
       to the abstract.
    6. Do not infer relations not explicitly stated or strongly implied in the text.
    """

    # Log process details
    logger.info(f"Process Name: {ProcessConfig.Process_name}")
    logger.debug(f"Process Description:\n{ProcessConfig.Process_description}")
    logger.debug(f"Process Constraints:\n{ProcessConfig.Process_property_constraints}")

    # Results directory
    results_dir = args.results_dir if args.results_dir else f"results/extractions/BioRED/experiment4/{args.data_split}"
    logger.info(f"Results Directory: {results_dir}")

    # Read the process schema from a JSON file
    process_schema_path = args.process_schema if args.process_schema else "data/schemas/BioRED/BioRED-schema.json"
    process_schema = read_json_file(process_schema_path)
    logger.info(f"Loaded process schema from: {process_schema_path}")

    # Read the gold-standard examples from a text file
    examples_path = args.process_examples if args.process_examples else "data/examples/BioRED/example1.txt"
    examples = read_text_file(examples_path)
    logger.info(f"Loaded process examples from: {examples_path}")

    # Load the dataset split
    data_path = f"data/gold-standard-datasets/BioRED/processed/{args.data_split}.json"
    data = read_json_file(data_path)
    logger.info(f"Loaded {len(data)} documents from: {data_path}")

    # Format the results directory path with LLM model name
    res_llm_model = ProviderRegistry.parse_llm_string(extraction_llm)[0].split("/")[-1]
    res_dir = f"{results_dir}/{res_llm_model}"

    # Process each document in the dataset
    for record in data:
        doc_id = str(record["doc_id"])
        text = record["text"]
        json_filename = f"{doc_id}.json"

        # Check if the extraction result already exists
        if os.path.exists(f"{res_dir}/{json_filename}"):
            logger.info(f"Extraction result already exists for document: {doc_id}. Skipping.")
            continue

        logger.info(f"Processing document: {doc_id}")

        # Initialize orchestrator configuration
        orchestrator_config = OrchestratorConfig(
            extraction_llm=extraction_llm,
            process_schema=process_schema,
            scientific_document=text,
            examples=examples,
            extraction_data_model=BioREDSchema,
            summarizer_llm=summarizer_llm,
            reflection_judge_llms=reflection_judge_llms.split(","),
            reflection_critic_llms=reflection_critic_llms.split(","),
            rubrics=[Completeness, Correctness],
            feedback_llm=feedback_llm
        )

        # Initialize the Workflow configuration
        workflow_config = WorkflowConfig(
            normalize_extracted_data=False,
            clean_extracted_data=False,
            validate_extracted_data=True,
            refine_extracted_data=True,
            reflection_mode="debate",
            total_validation_retries=2
        )

        # Extract knowledge using the orchestrator agent
        final_state = orchestrate_extraction_workflow(orchestrator_config, workflow_config)
        logger.info(f"Extraction completed for document: {doc_id}")

        # Get the extracted knowledge from the final state
        extracted_knowledge = final_state["extracted_json"]

        # Save the extracted information to a JSON file
        file_saved = save_json_file(res_dir, json_filename, extracted_knowledge)
        if not file_saved: raise Exception(f"Failed to save extracted information for document: {doc_id}")
        logger.info(f"Extracted information saved to: {res_dir}/{json_filename}")

    logger.info("BioRED information extraction with debate refinement completed for all documents.")
