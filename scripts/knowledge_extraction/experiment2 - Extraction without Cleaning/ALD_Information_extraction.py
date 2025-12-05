"""
Script to extract structured ALD process information from scientific documents (Used in Schema-miner) based on ALD experimental/Simulation schema. This script only extracts the information without cleaning and normalization using the SciKG-Extract framework.

Author: Sameer Sadruddin
Created: November 26, 2025
Last Modified: November 26, 2025
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

# Data Model for ALD Experimental and Simulation Use Case
from data.models.schema.ALD_experimental_schema import ALDProcessList
from data.models.schema.ALD_simulation_schema import ALDSimulationProcessList

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
    llm_model = args.llm_model if args.llm_model else "mistral-large-instruct"
    logger.info(f"Using LLM model: {llm_model}")

    # Updating the process description for ALD
    ProcessConfig.Process_description = """
    Atomic Layer Deposition (ALD) is a thin-film fabrication technique that relies on sequential, self-limiting surface reactions to produce highly uniform and conformal coatings, even over complex 3D structures. In simulation use cases, ALD is modeled to understand how precursor chemistry, surface kinetics, temperature, and reactor flow dynamics influence film growth at the atomic scale. Simulations help predict growth-per-cycle, film uniformity, defect formation, and precursor diffusion behavior, enabling optimization of process parameters before physical experimentation. This accelerates materials development, reduces trial-and-error costs, and supports the design of advanced semiconductor, energy, and nanotechnology devices.
    """

    # Log process details
    logger.info(f"Process Name: {ProcessConfig.Process_name}")
    logger.debug(f"Process Description:\n{ProcessConfig.Process_description}")
    logger.debug(f"Process Contraints:\n{ProcessConfig.Process_property_constraints}")

    # Results directory
    results_dir = args.results_dir if args.results_dir else "results/extracted-data/ALD/version2/Others/experimental-usecase"
    logger.info(f"Results Directory to save extracted data: {results_dir}")

    # Read the process schema from the JSON file
    process_schema_path = args.process_schema if args.process_schema else "data/schemas/ALD-experimental/ALD-experimental-schema.json"
    process_schema = read_json_file(process_schema_path)
    logger.info(f"Loaded process schema from: {process_schema_path}")

    # Read the gold-standard examples from a text file
    examples_path = args.process_examples if args.process_examples else "data/examples/Atomic-layer-deposition/ZnO/example1.txt"
    examples = read_text_file(examples_path)
    logger.info(f"Loaded process examples from: {examples_path}")

    # Directory containing scientific documents
    scientific_docs_dir = args.scientific_docs_dir if args.scientific_docs_dir else "data/research-papers/ALD/markdown/Others/experimental-usecase"
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

            # Format the results directory path for the current document and JSON filename
            res_dir = f"{results_dir}{root.split(scientific_docs_dir)[-1].replace("\\", "/").strip()}/{llm_model}"
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
                llm_name=llm_model,
                process_schema=process_schema,
                scientific_document=scientific_document,
                examples=examples,
                extraction_data_model=ALDSimulationProcessList,
                pubchem_lmdb_path="",
                synonym_to_cid_mapping={},
                reflection_llm_name="",
                rubrics=[],
                feedback_llm_name=""
            )

            # Initialize the Workflow configuration
            workflow_config = WorkflowConfig(
                normalize_extracted_data=False,
                clean_extracted_data=False,
                validate_extracted_data=False
            )

            # Extract knowledge using the orchestrator agent
            extracted_knowledge = orchestrate_extraction_workflow(orchestrator_config, workflow_config)
            logger.info(f"Extraction completed for document: {root}/{filename}")

            # Save the extracted information to a JSON file
            file_saved = save_json_file(res_dir, json_filename, extracted_knowledge)
            if not file_saved: raise Exception(f"Failed to save extracted information for document: {filename}")
            logger.info(f"Extracted information saved to: {res_dir}/{json_filename}")