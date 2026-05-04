"""
Script to extract structured materials synthesis procedure information from PcMSP dataset sentences. This script performs extraction only (no reflection or refinement) using the SciKG-Extract framework.
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

# Data model for PcMSP
from data.models.schema.pcmsp_schema import PcMSPSchema

if __name__ == "__main__":
    """Main function to extract materials synthesis procedure information from PcMSP sentences."""

    # Argument Parser Setup
    parser = argparse.ArgumentParser(description="Extract structured materials synthesis information from PcMSP dataset.")
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
    logger.info("Starting PcMSP information extraction script...")
    logger.info(f"Using extraction LLM: {extraction_llm}")

    # Override ProcessConfig for PcMSP
    ProcessConfig.Process_name = "Materials Synthesis Procedure Extraction"
    ProcessConfig.Process_description = """
    The PcMSP (Procedural text corpus for Materials Synthesis Procedures) task involves extracting structured information about materials synthesis procedures from scientific text at the sentence level. Each sentence may describe synthesis steps including materials used, operations performed, experimental conditions, and equipment. The goal is to identify entities across seven categories (materials with subtypes, operations, descriptors, values, properties, devices, brands) and the relations between them (e.g., which descriptor applies to which operation, which value corresponds to which property).
    """
    ProcessConfig.Process_property_constraints = """
    1. Entity categories: Extract entities in exactly these 7 categories:
       - materials: with subtypes (Material-target, Material-recipe, Material-others)
       - operations: synthesis/processing steps (e.g., "heated", "stirred", "dried")
       - descriptors: qualitative descriptions (e.g., "slowly", "dropwise", "overnight")
       - values: numerical values with units (e.g., "500 °C", "2 hours", "10 mL")
       - properties: measured or target properties (e.g., "temperature", "particle size")
       - devices: equipment used (e.g., "furnace", "autoclave")
       - brands: manufacturer or brand names (e.g., "Sigma-Aldrich")
    2. Material subtypes: Each material must have a subtype of Material-target, Material-recipe, or Material-others.
    3. Relation types: Extract relations of these 8 types: Operation-Descriptor, Operation-Value, Operation-Device,
       Operation-Material, Value-Descriptor, Property-Value, Brand-Material, Brand-Device.
    4. Extraction is at the sentence level: extract entities and relations from each sentence independently.
    5. Use exact text spans from the sentence for entity text values.
    """

    # Log process details
    logger.info(f"Process Name: {ProcessConfig.Process_name}")
    logger.debug(f"Process Description:\n{ProcessConfig.Process_description}")
    logger.debug(f"Process Constraints:\n{ProcessConfig.Process_property_constraints}")

    # Results directory
    results_dir = args.results_dir if args.results_dir else f"results/extractions/PcMSP/experiment1/{args.data_split}"
    logger.info(f"Results Directory: {results_dir}")

    # Read the process schema from a JSON file
    process_schema_path = args.process_schema if args.process_schema else "data/schemas/PcMSP/PcMSP-schema.json"
    process_schema = read_json_file(process_schema_path)
    logger.info(f"Loaded process schema from: {process_schema_path}")

    # Read the gold-standard examples from a text file
    examples_path = args.process_examples if args.process_examples else "data/examples/PcMSP/example1.txt"
    examples = read_text_file(examples_path)
    logger.info(f"Loaded process examples from: {examples_path}")

    # Load the dataset split
    data_path = f"data/gold-standard-datasets/PcMSP/processed/{args.data_split}.json"
    data = read_json_file(data_path)
    logger.info(f"Loaded {len(data)} sentences from: {data_path}")

    # Format the results directory path with LLM model name
    res_llm_model = ProviderRegistry.parse_llm_string(extraction_llm)[0].split("/")[-1]
    res_dir = f"{results_dir}/{res_llm_model}"

    # Process each sentence in the dataset
    for record in data:
        sent_id = str(record["sent_id"])
        text = record["text"]
        json_filename = f"{sent_id}.json"

        # Check if the extraction result already exists
        if os.path.exists(f"{res_dir}/{json_filename}"):
            logger.info(f"Extraction result already exists for sentence: {sent_id}. Skipping.")
            continue

        logger.info(f"Processing sentence: {sent_id}")

        # Initialize orchestrator configuration
        orchestrator_config = OrchestratorConfig(
            extraction_llm=extraction_llm,
            process_schema=process_schema,
            scientific_document=text,
            examples=examples,
            extraction_data_model=PcMSPSchema
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
        logger.info(f"Extraction completed for sentence: {sent_id}")

        # Get the extracted knowledge from the final state
        extracted_knowledge = final_state["extracted_json"]

        # Save the extracted information to a JSON file
        file_saved = save_json_file(res_dir, json_filename, extracted_knowledge)
        if not file_saved: raise Exception(f"Failed to save extracted information for sentence: {sent_id}")
        logger.info(f"Extracted information saved to: {res_dir}/{json_filename}")

    logger.info("PcMSP information extraction completed for all sentences.")
