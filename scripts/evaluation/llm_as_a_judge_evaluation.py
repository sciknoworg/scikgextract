"""
Script to evaluate extracted structured knowledge using the LLM-as-a-Judge paradigm. The LLM acts as a judge to assess the quality of the extracted knowledge based on predefined rubrics.

Author: Sameer Sadruddin
Created: November 27, 2025
Last Modified: November 27, 2025
"""
# Python packages
import os
import json
import argparse

# SciKG-Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import read_json_file, read_text_file, save_json_file

# SciKG-Extract Agent Imports
from scikg_extract.agents.states import ExtractionState
from scikg_extract.agents.reflection_agent import validate_extracted_processes

# SciKG-Extract Config Imports
from scikg_extract.config.process.processConfig import ProcessConfig
from scikg_extract.config.agents.reflection import ReflectionConfig

# SciKG-Extract Evaluation Rubric Imports
from scikg_extract.evaluation.rubrics.informativeness import Correctness
from scikg_extract.evaluation.rubrics.informativeness import Completeness

if __name__ == "__main__":
    """Main function to evaluate extracted structured knowledge using LLM-as-a-Judge paradigm."""

    # Argument Parser Setup
    parser = argparse.ArgumentParser(description="Evaluate extracted structured knowledge using LLM-as-a-Judge paradigm.")
    parser.add_argument("--llm_model", type=str, required=False, help="The large language model to be used as a Judge in the evaluation.")
    parser.add_argument("--extracted_data_path", type=str, required=False, help="Path to the extracted structured knowledge JSON files.")
    parser.add_argument("--scientific_document_path", type=str, required=False, help="Path to the scientific documents in the markdown format.")
    parser.add_argument("--results_dir", type=str, required=False, help="Directory to save the evaluation results.")
    parser.add_argument("--process_schema_path", type=str, required=False, help="Path to the process schema JSON file.")

    # Parse the arguments
    args = parser.parse_args()

    # Configure and Initialize logging
    logger = LogHandler.setup_module_logging("scikg_extract")
    logger.info("Starting LLM-as-a-Judge evaluation script...")

    # Extracted Information path
    extracted_data_path = args.extracted_data_path if args.extracted_data_path else "results/extracted-data/ALD/version2/ZnO-IGZO-papers/experimental-usecase/IGZO"
    logger.info(f"Extracted data path: {extracted_data_path}")

    # Scientific document path
    scientific_document_path = args.scientific_document_path if args.scientific_document_path else "data/research-papers/ALD/markdown"
    logger.info(f"Scientific document path: {scientific_document_path}")

    # Read the process schema
    process_schema_path = args.process_schema_path if args.process_schema_path else "data/schemas/ALD-experimental/ALD-experimental-schema.json"
    process_schema = read_json_file(process_schema_path)
    logger.info(f"Process schema loaded from: {process_schema_path}")

    # Results directory
    results_dir = args.results_dir if args.results_dir else "results/evaluation"
    logger.info(f"Results directory for evaluation: {results_dir}")

    # LLM model to use for evaluation
    llm_model = args.llm_model if args.llm_model else "gpt-5"
    logger.info(f"Using LLM model for evaluation: {llm_model}")

    # Update ProcessConfig with the process details
    ProcessConfig.Process_description = """
    Atomic layer deposition (ALD) is a surface-controlled thin film deposition technique that can enable ultimate control over the film thickness, uniformity on large-area substrates and conformality on 3D (nano)structures. Each ALD cycle consists at least two half-cycles (but can be more complex), containing a precursor dose step and a co-reactant exposure step, separated by purge or pump steps. Ideally the same amount of material is deposited in each cycle, due to the self-limiting nature of the reactions of the precursor and co-reactant with the surface groups on the substrate. By carrying out a certain number of ALD cycles, the targeted film thickness can be obtained.

    In this extraction task, we are focusing on IGZO (Indium Gallium Zinc Oxide) thin film deposition via ALD. An IGZO ALD process is a supercycle-based thin-film deposition method used to form multicomponent oxide layers composed of indium oxide (In2O3), gallium oxide (Ga2O3), and zinc oxide (ZnO). The process deposits IGZO by sequentially repeating ALD sub-cycles of the individual metal oxides in a defined ratio. Each sub-cycle typically consists of a metal precursor pulse, a purge, an oxidant pulse (such as H2O, O3, or O2 plasma), and a second purge. A single IGZO supercycle is composed of a cycles of In2O3, b cycles of Ga2O3, and c cycles of ZnO, where the a:b:c ratio controls the IGZO film composition, electrical properties, and oxygen-vacancy concentration.

    Different precursors are used for each element. For example, diethylzinc (DEZ) and trimethylgallium (TMGa) are common for zinc and gallium, respectively, while a precursor like 3-(dimethylamino)propyl)dimethylindium (DADI) is used for indium. The goal of an IGZO ALD process is to produce a conformal, composition-controlled, amorphous IGZO film suitable for applications such as thin-film transistors (TFTs).
    """

    # Iterate over each extracted data file for evaluation
    for root, _, files in os.walk(extracted_data_path):

        # Skip if no files found
        if not files: continue

        # Check if all files are JSON files
        json_files = all(file.endswith(".json") for file in files)
        if not json_files:
            logger.warning(f"Non-JSON files found in directory: {root}. Skipping this directory.")
            continue

        # Format and Check scientific document path
        scientific_doc_dir = f"{scientific_document_path}{root.split("version2")[-1]}"
        scientific_doc_dir = scientific_doc_dir.replace("\\", "/").strip()
        scientific_doc_dir = "/".join(scientific_doc_dir.split("/")[:-1])

        # Process each JSON file in the directory
        for file in files:
            json_filepath = f"{root}/{file}"
            logger.info(f"Evaluating extracted data file: {json_filepath}")

            # Format the results directory path for the current document and JSON filename
            res_dir = f"{results_dir}{root.split("extracted-data")[-1]}/{llm_model}".replace("\\", "/").strip()
            evaluation_filename = f"{os.path.splitext(file)[0]}_evaluation.json"

            # Check if evaluation result already exists
            if os.path.exists(f"{res_dir}/{evaluation_filename}"):
                logger.info(f"Evaluation result already exists for file: {json_filepath}. Skipping evaluation.")
                continue

            # Read the extracted structured knowledge JSON file
            extracted_data = read_json_file(json_filepath)
            logger.info("Extracted data loaded successfully.")

            # Derive the corresponding scientific document filepath
            scientific_document_filename = f"{os.path.splitext(file)[0]}.md"
            scientific_document_filepath = f"{scientific_doc_dir}/{scientific_document_filename}"

            # Read the scientific document in markdown format
            scientific_document = read_text_file(scientific_document_filepath)
            logger.info(f"Scientific document loaded successfully: {scientific_document_filepath}")

            # Define the initial state for evaluation
            initial_state = ExtractionState(
                process_name=ProcessConfig.Process_name,
                process_description=ProcessConfig.Process_description,
                process_property_constraints=ProcessConfig.Process_property_constraints,
                scientific_document=scientific_document,
                process_schema=process_schema,
                extracted_json=extracted_data,
                validation_llm_model=llm_model,
            )
            logger.info("Initial evaluation state defined successfully.")

            # Initialize the Reflection configuration
            reflection_config = ReflectionConfig(
                llm_name=llm_model,
                rubric_names=[Correctness, Completeness]
            )
            logger.info("Reflection configuration initialized successfully.")

            # Execute the validation agent to evaluate the extracted processes
            final_state = validate_extracted_processes(reflection_config, initial_state)
            logger.info(f"Evaluation completed using LLM-as-a-Judge paradigm for file: {json_filepath}")

            # Save the evaluation results
            file_saved = save_json_file(res_dir, evaluation_filename, final_state["evaluation_results"])
            if not file_saved: raise Exception(f"Failed to save evaluation results for file: {json_filepath}")
            logger.info(f"Evaluation results saved to: {res_dir}/{evaluation_filename}")