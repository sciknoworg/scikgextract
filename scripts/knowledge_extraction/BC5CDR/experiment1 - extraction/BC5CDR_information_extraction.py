"""
Script to extract structured chemical-disease relation information from BC5CDR dataset abstracts. This script performs extraction only (no reflection or refinement) using the SciKG-Extract framework.
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

# Data model for BC5CDR
from data.models.schema.bc5cdr_schema import BC5CDRSchema

if __name__ == "__main__":
    """Main function to extract chemical-disease relation information from BC5CDR abstracts."""

    # Argument Parser Setup
    parser = argparse.ArgumentParser(description="Extract structured chemical-disease relation information from BC5CDR dataset.")
    parser.add_argument("--extraction_llm", type=str, help="The LLM to use for extraction in format 'PROVIDER:model_name' (e.g., 'OPENAI:gpt-4o').")
    parser.add_argument("--results_dir", type=str, help="Directory to save the extracted data.")
    parser.add_argument("--process_schema", type=str, help="Path to the process schema JSON file.")
    parser.add_argument("--process_examples", type=str, help="Path to the gold-standard examples text file.")
    parser.add_argument("--data_split", type=str, default="test", help="Data split to process: train, val, or test (default: test).")

    # Parse the arguments
    args = parser.parse_args()

    # Initialize the extraction LLM
    extraction_llm = args.extraction_llm if args.extraction_llm else "OPENAI:gpt-4o"

    # Build unique run identifier for concurrent execution (LLM name + PID)
    run_id = f"{extraction_llm}_{os.getpid()}"

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("scikg_extract", run_id=run_id)
    logger.info("Starting BC5CDR information extraction script...")
    logger.info(f"Using extraction LLM: {extraction_llm}")

    # Override ProcessConfig for BC5CDR
    ProcessConfig.Process_name = "Chemical-Disease Relation Extraction"
    ProcessConfig.Process_description = """
    The BC5CDR (BioCreative V Chemical Disease Relation) task involves extracting chemical and disease named entities from biomedical abstracts, along with their Chemical-Induced Disease (CID) relationships. Each abstract may mention multiple chemicals and diseases. The goal is to identify all chemical entities (with MeSH identifiers), all disease entities (with MeSH identifiers), and any CID relations where a chemical is reported to induce or cause a disease.
    """
    ProcessConfig.Process_property_constraints = """
    1. Entity types: Extract only "Chemical" and "Disease" entities.
    2. Identifiers: Each entity should have a MeSH identifier (e.g., "D015738" for Famotidine).
    3. Offsets: Include character offset and length for each entity mention in the text.
    4. Relations: Only extract Chemical-Induced Disease (CID) relations where a chemical causes or induces a disease.
    5. Relation format: Each relation links a chemical entity text to a disease entity text with type "CID".
    6. Do not infer relations that are not explicitly stated or strongly implied in the text.
    """

    # Log process details
    logger.info(f"Process Name: {ProcessConfig.Process_name}")
    logger.debug(f"Process Description:\n{ProcessConfig.Process_description}")
    logger.debug(f"Process Constraints:\n{ProcessConfig.Process_property_constraints}")

    # Results directory
    results_dir = args.results_dir if args.results_dir else f"results/extractions/BC5CDR/experiment1/{args.data_split}"
    logger.info(f"Results Directory: {results_dir}")

    # Read the process schema from a JSON file
    process_schema_path = args.process_schema if args.process_schema else "data/schemas/BC5CDR/BC5CDR-schema.json"
    process_schema = read_json_file(process_schema_path)
    logger.info(f"Loaded process schema from: {process_schema_path}")

    # Read the gold-standard examples from a text file
    examples_path = args.process_examples if args.process_examples else "data/examples/BC5CDR/example1.txt"
    examples = read_text_file(examples_path)
    logger.info(f"Loaded process examples from: {examples_path}")

    # Load the dataset split
    data_path = f"data/gold-standard-datasets/BC5CDR/processed/{args.data_split}.json"
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
            extraction_data_model=BC5CDRSchema
        )

        # Initialize the Workflow configuration
        workflow_config = WorkflowConfig(
            normalize_extracted_data=False,
            clean_extracted_data=False,
            validate_extracted_data=False,
            refine_extracted_data=False
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

    logger.info("BC5CDR information extraction completed for all documents.")
