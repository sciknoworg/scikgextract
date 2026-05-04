"""
Script to extract structured polymer property information from PolyIE dataset documents with self-refinement using single reflection mode.
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

# Data model for PolyIE
from data.models.schema.polyie_schema import PolyIESchemaList

if __name__ == "__main__":
    """Main function to extract polymer property information from PolyIE documents with self-refinement."""

    # Argument Parser Setup
    parser = argparse.ArgumentParser(description="Extract structured polymer property information from PolyIE dataset with self-refinement.")
    parser.add_argument("--extraction_llm", type=str, help="The LLM to use for extraction in format 'PROVIDER:model_name' (e.g., 'OPENAI:gpt-4o').")
    parser.add_argument("--reflection_llm", type=str, help="The LLM to use for reflection in format 'PROVIDER:model_name' (e.g., 'OPENAI:gpt-5').")
    parser.add_argument("--feedback_llm", type=str, help="The LLM to use for feedback in format 'PROVIDER:model_name' (e.g., 'SAIA:meta-llama/llama-3.3-70b-instruct').")
    parser.add_argument("--results_dir", type=str, help="Directory to save the extracted data.")
    parser.add_argument("--process_schema", type=str, help="Path to the process schema JSON file.")
    parser.add_argument("--process_examples", type=str, help="Path to the gold-standard examples text file.")
    parser.add_argument("--data_split", type=str, default="test", help="Data split to process: train, val, or test (default: test).")

    # Parse the arguments
    args = parser.parse_args()

    # Initialize the LLMs
    extraction_llm = args.extraction_llm if args.extraction_llm else "OPENAI:gpt-4o"
    reflection_llm = args.reflection_llm if args.reflection_llm else "OPENAI:gpt-4o"
    feedback_llm = args.feedback_llm if args.feedback_llm else "OPENAI:gpt-4o"

    # Build unique run identifier for concurrent execution (LLM name + PID)
    run_id = f"{extraction_llm}_{os.getpid()}"

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("scikg_extract", run_id=run_id)
    logger.info("Starting PolyIE information extraction script with self-refinement in single reflection mode...")
    logger.info(f"Using extraction LLM: {extraction_llm}")
    logger.info(f"Using reflection LLM: {reflection_llm}")
    logger.info(f"Using feedback LLM: {feedback_llm}")

    # Override ProcessConfig for PolyIE
    ProcessConfig.Process_name = "Polymer Information Extraction"
    ProcessConfig.Process_description = """
    The PolyIE (Polymer Information Extraction) task involves extracting structured property information about polymers and chemical compounds from scientific text. Each document contains multiple sentences describing polymer synthesis, characterization, and device performance. The goal is to identify chemical names (polymers, monomers, blends), property names (e.g., PCE, Voc, Jsc, FF, band gap), property values (numerical measurements with units), and experimental conditions, then link them via n-ary relations that associate a chemical with its measured properties and values.
    """
    ProcessConfig.Process_property_constraints = """
    1. Entity categories: Extract entities in exactly these 4 categories:
       - chemicalNames: polymer names, abbreviations, chemical compounds, blend compositions (e.g., "PNDFT-DTBT:PC61BM")
       - propertyNames: measured or reported properties (e.g., "PCE", "Voc", "Jsc", "FF", "band gap")
       - propertyValues: numerical values with units (e.g., "5.22%", "0.89 V", "8.21 mA cm^-2")
       - conditions: experimental conditions (e.g., temperature, atmosphere, solvent)
    2. Relations are n-ary tuples: each relation links a chemicalName to a propertyName and propertyValue,
       with an optional condition field.
    3. The condition field should be null if no specific condition is associated with the measurement.
    4. Extract information from the full document text (all sentences combined).
    5. Chemical names include polymer abbreviations, blend ratios, and common chemical names.
    6. Use exact text spans from the document for entity values where possible.
    """

    # Log process details
    logger.info(f"Process Name: {ProcessConfig.Process_name}")
    logger.debug(f"Process Description:\n{ProcessConfig.Process_description}")
    logger.debug(f"Process Constraints:\n{ProcessConfig.Process_property_constraints}")

    # Results directory
    results_dir = args.results_dir if args.results_dir else f"results/extractions/PolyIE/experiment2/{args.data_split}"
    logger.info(f"Results Directory: {results_dir}")

    # Read the process schema from a JSON file
    process_schema_path = args.process_schema if args.process_schema else "data/schemas/PolyIE/PolyIE-schema.json"
    process_schema = read_json_file(process_schema_path)
    logger.info(f"Loaded process schema from: {process_schema_path}")

    # Read the gold-standard examples from a text file
    examples_path = args.process_examples if args.process_examples else "data/examples/PolyIE/example1.txt"
    examples = read_text_file(examples_path)
    logger.info(f"Loaded process examples from: {examples_path}")

    # Load the dataset split
    data_path = f"data/gold-standard-datasets/PolyIE/processed/{args.data_split}.json"
    data = read_json_file(data_path)
    logger.info(f"Loaded {len(data)} documents from: {data_path}")

    # Format the results directory path with LLM model name
    res_llm_model = ProviderRegistry.parse_llm_string(extraction_llm)[0].split("/")[-1]
    res_dir = f"{results_dir}/{res_llm_model}"

    # Process each document in the dataset
    for record in data:
        doc_id = str(record["doc_id"])
        json_filename = f"{doc_id}.json"

        # Concatenate all sentence texts to form the full document
        text = " ".join([sent["text"] for sent in record["sentences"]])

        # Check if the extraction result already exists
        if os.path.exists(f"{res_dir}/{json_filename}"):
            logger.info(f"Extraction result already exists for document: {doc_id}. Skipping.")
            continue

        logger.info(f"Processing document: {doc_id} ({len(record['sentences'])} sentences)")

        # Initialize orchestrator configuration
        orchestrator_config = OrchestratorConfig(
            extraction_llm=extraction_llm,
            process_schema=process_schema,
            scientific_document=text,
            examples=examples,
            extraction_data_model=PolyIESchemaList,
            reflection_llm=reflection_llm,
            rubrics=[Completeness, Correctness],
            feedback_llm=feedback_llm
        )

        # Initialize the Workflow configuration
        workflow_config = WorkflowConfig(
            normalize_extracted_data=False,
            clean_extracted_data=False,
            validate_extracted_data=True,
            refine_extracted_data=True,
            reflection_mode="single",
            total_validation_retries=5
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

    logger.info("PolyIE information extraction with self-refinement completed for all documents.")
