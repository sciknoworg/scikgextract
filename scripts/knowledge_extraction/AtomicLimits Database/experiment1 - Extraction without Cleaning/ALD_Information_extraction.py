"""
Script to extract structured ALD process information from scientific documents based on ALD experimental/Simulation schema. This script only extracts the information without cleaning and normalization using the SciKG-Extract framework.
"""
# Python imports
import os
import argparse

# Scikg_extract utility imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import read_json_file, read_text_file, save_json_file

# Scikg_extract agent imports
from scikg_extract.agents.orchestrator_agent import orchestrate_extraction_workflow

# Scikg_extract config imports
from scikg_extract.config.process.processConfig import ProcessConfig
from scikg_extract.config.agents.orchestrator import OrchestratorConfig
from scikg_extract.config.agents.workflow import WorkflowConfig

# Data model for ALD Experimental Use case
from data.models.schema.ALD_experimental_schema import ALDProcessList

if __name__ == "__main__":
    """Main function to extract ALD process information from scientific documents."""

    # Argument Parser Setup
    parser = argparse.ArgumentParser(description="Extract structured ALD process information from scientific documents.")
    parser.add_argument("--llm_model", type=str, help="The name of the large language model to use.")
    parser.add_argument("--results_dir", type=str, help="Directory to save the extracted data.")
    parser.add_argument("--process_schema", type=str, help="Path to the process schema JSON file.")
    parser.add_argument("--process_examples", type=str, help="Path to the gold-standard examples text file.")
    parser.add_argument("--scientific_docs_dir", type=str, help="Directory containing scientific documents in text/markdown format.")

    # Parse the arguments
    args = parser.parse_args()

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("scikg_extract")
    logger.info("Starting ALD information extraction script...")

    # Initialize the LLM model
    llm_model = args.llm_model if args.llm_model else "SAIA:meta-llama/llama-3.3-70b-instruct"
    logger.info(f"Using LLM model: {llm_model}")

    # Log process details
    logger.info(f"Process Name: {ProcessConfig.Process_name}")
    logger.debug(f"Process Description:\n{ProcessConfig.Process_description}")
    logger.debug(f"Process Contraints:\n{ProcessConfig.Process_property_constraints}")

    # Results directory
    results_dir = args.results_dir if args.results_dir else "results/extractions/AtomicLimits Database/ALD/version1"
    logger.info(f"Results Directory to save extracted data: {results_dir}")

    # Read the process schema from a JSON file
    process_schema_path = args.process_schema if args.process_schema else "data/schemas/ALD/experimental-usecase/ALD-experimental-schema.json"
    process_schema = read_json_file(process_schema_path)
    logger.info(f"Loaded process schema from: {process_schema_path}")

    # Read the gold-standard examples from a text file
    examples_path = args.process_examples if args.process_examples else "data/examples/ALD/ZnO/example1.txt"
    examples = read_text_file(examples_path)
    logger.info(f"Loaded process examples from: {examples_path}")

    # Directory containing scientific documents
    scientific_docs_dir = args.scientific_docs_dir if args.scientific_docs_dir else "data/research-papers/ALD/markdown/AtomicLimits Database"
    logger.info(f"Scientific Documents Directory: {scientific_docs_dir}")

    # Process each scientific document in the specified directory
    for root, _, filenames in os.walk(scientific_docs_dir):

        # Skip if no files found
        if not filenames: continue

        # Process each file in the directory
        for filename in filenames:
        
            # Process only markdown or text files
            if not filename.endswith(".md") and not filename.endswith(".txt"): 
                logger.debug(f"Skipping non-markdown/text file: {filename}")
                continue

            if filename == '38 Puurunen et al.md': continue

            # Format the results directory path for the current document and JSON filename
            res_llm_model = llm_model.split("/")[-1]
            res_dir = f"{results_dir}{root.split(scientific_docs_dir)[-1].replace("\\", "/").strip()}/{res_llm_model}"
            json_filename = f"{os.path.splitext(filename)[0]}.json"

            # Check if the extraction result already exists
            if os.path.exists(f"{res_dir}/{json_filename}"):
                logger.info(f"Extraction result already exists for document: {filename}. Skipping extraction.")
                continue

            # Read the scientific document in markdown format
            logger.info(f"Processing scientific document: {filename}")
            scientific_document_filepath = f"{root}/{filename}"
            scientific_document = read_text_file(scientific_document_filepath)

            # Initialize orchestrator configuration
            orchestrator_config = OrchestratorConfig(
                extraction_llm=llm_model,
                process_schema=process_schema,
                scientific_document=scientific_document,
                examples=examples,
                extraction_data_model=ALDProcessList
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
            logger.info(f"Extraction completed for document: {root}/{filename}")

            # Get the extracted knowledge from the final state
            extracted_knowledge = final_state["extracted_json"]

            # Save the extracted information to a JSON file
            file_saved = save_json_file(res_dir, json_filename, extracted_knowledge)
            if not file_saved: raise Exception(f"Failed to save extracted information for document: {filename} at directory: {res_dir}")
            logger.info(f"Extracted information saved to: {res_dir}/{json_filename}")