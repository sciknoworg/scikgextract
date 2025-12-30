"""
Script to extract structured ALD process information related to IGZO thin-film deposition from scientific documents based on ALD experimental schema. This script only extracts the information and perform normalization without cleaning the final extracted data using SciKG-Extract framework.

Author: Sameer Sadruddin
Created: November 16, 2025
Last Modified: December 20, 2025
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

# Data Model for ALD Experimental Use Case
from data.models.schema.ALD_experimental_schema import ALDProcessList

if __name__ == "__main__":
    """Main function to extract ALD IGZO process information from scientific documents."""

    # Argument Parser Setup
    parser = argparse.ArgumentParser(description="Extract structured ALD process information from scientific documents.")
    parser.add_argument("--llm_model", type=str, help="The name of the large language model to use.")
    parser.add_argument("--normalization_llm_model", type=str, help="The name of the LLM model to use for normalization disambiguation.")
    parser.add_argument("--results_dir", type=str, help="Directory to save the extracted data.")
    parser.add_argument("--normalized_results_dir", type=str, help="Directory to save the normalized extracted data.")
    parser.add_argument("--process_schema", type=str, help="Path to the process schema JSON file.")
    parser.add_argument("--process_examples", type=str, help="Path to the gold-standard examples text file.")
    parser.add_argument("--scientific_docs_dir", type=str, help="Directory containing scientific documents in text/markdown format.")
    parser.add_argument("--pubchem_lookup_dict_path", type=str, help="Path to the manual curated PubChem CID mapping lookup dictionary JSON file.")
    parser.add_argument("--lmdb_pubchem_path", type=str, help="Path to the LMDB PubChem CID mapping database.")

    # Parse the arguments
    args = parser.parse_args()

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("scikg_extract")
    logger.info("Starting ALD information extraction script for IGZO...")

    # Initialize the LLM model
    llm_model = args.llm_model if args.llm_model else "gpt-4o"
    logger.info(f"Using LLM model: {llm_model}")

    # Initialize the Normalization LLM model
    normalization_llm_model = args.normalization_llm_model if args.normalization_llm_model else "gpt-5"
    logger.info(f"Using Normalization LLM model: {normalization_llm_model}")

    # Updating the process description for IGZO
    ProcessConfig.Process_description = """
    Atomic layer deposition (ALD) is a surface-controlled thin film deposition technique that can enable ultimate control over the film thickness, uniformity on large-area substrates and conformality on 3D (nano)structures. Each ALD cycle consists at least two half-cycles (but can be more complex), containing a precursor dose step and a co-reactant exposure step, separated by purge or pump steps. Ideally the same amount of material is deposited in each cycle, due to the self-limiting nature of the reactions of the precursor and co-reactant with the surface groups on the substrate. By carrying out a certain number of ALD cycles, the targeted film thickness can be obtained.

    In this extraction task, we are focusing on IGZO (Indium Gallium Zinc Oxide) thin film deposition via ALD. An IGZO ALD process is a supercycle-based thin-film deposition method used to form multicomponent oxide layers composed of indium oxide (In2O3), gallium oxide (Ga2O3), and zinc oxide (ZnO). The process deposits IGZO by sequentially repeating ALD sub-cycles of the individual metal oxides in a defined ratio. Each sub-cycle typically consists of a metal precursor pulse, a purge, an oxidant pulse (such as H2O, O3, or O2 plasma), and a second purge. A single IGZO supercycle is composed of a cycles of In2O3, b cycles of Ga2O3, and c cycles of ZnO, where the a:b:c ratio controls the IGZO film composition, electrical properties, and oxygen-vacancy concentration.

    Different precursors are used for each element. For example, diethylzinc (DEZ) and trimethylgallium (TMGa) are common for zinc and gallium, respectively, while a precursor like 3-(dimethylamino)propyl)dimethylindium (DADI) is used for indium. The goal of an IGZO ALD process is to produce a conformal, composition-controlled, amorphous IGZO film suitable for applications such as thin-film transistors (TFTs).
    """

    # Log process details
    logger.info(f"Process Name: {ProcessConfig.Process_name}")
    logger.debug(f"Process Description:\n{ProcessConfig.Process_description}")
    logger.debug(f"Process Contraints:\n{ProcessConfig.Process_property_constraints}")

    # Results directory
    results_dir = args.results_dir if args.results_dir else "results/extracted-data-test/ALD/version1/ZnO-IGZO-papers/experimental-usecase/IGZO"
    logger.info(f"Results Directory to save extracted data: {results_dir}")

    # Normalized results directory
    normalized_results_dir = args.normalized_results_dir if args.normalized_results_dir else "results/extracted-data-test/ALD/version2/ZnO-IGZO-papers/experimental-usecase/IGZO"
    logger.info(f"Normalized Results Directory to save normalized extracted data: {normalized_results_dir}")

    # Read the process schema from the JSON file
    process_schema_path = args.process_schema if args.process_schema else "data/schemas/ALD-experimental/ALD-experimental-schema.json"
    process_schema = read_json_file(process_schema_path)
    logger.info(f"Loaded process schema from: {process_schema_path}")

    # Read the gold-standard examples from a text file
    examples_path = args.process_examples if args.process_examples else "data/examples/Atomic-layer-deposition/IGZO/example1.txt"
    examples = read_text_file(examples_path)
    logger.info(f"Loaded process examples from: {examples_path}")

    # Load manual curated PubChem CID mapping lookup dictionary
    pubchem_lookup_dict_path = args.pubchem_lookup_dict_path if args.pubchem_lookup_dict_path else "data/resources/PubChem-Synonym-CID.json"
    synonym_to_cid_mapping = read_json_file(pubchem_lookup_dict_path)
    logger.info(f"Loaded PubChem CID mapping lookup dictionary with {len(synonym_to_cid_mapping)} entries from: {pubchem_lookup_dict_path}")

    # LMDB PubChem CID mapping path
    lmdb_pubchem_path = args.lmdb_pubchem_path if args.lmdb_pubchem_path else "data/external/pubchem/pubchem_cid_lmdb"

    # Directory containing scientific documents
    scientific_docs_dir = args.scientific_docs_dir if args.scientific_docs_dir else "data/research-papers/ALD/markdown/ZnO-IGZO-papers/experimental-usecase/IGZO"
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
            norm_results_dir = f"{normalized_results_dir}{root.split(scientific_docs_dir)[-1].replace('\\', '/').strip()}/{llm_model}"
            json_filename = f"{os.path.splitext(filename)[0]}.json"

            # Check if the extraction result already exists
            if os.path.exists(f"{res_dir}/{json_filename}") and os.path.exists(f"{norm_results_dir}/{json_filename}"):
                logger.info(f"Extraction result already exists for document: {filename}. Skipping extraction.")
                continue

            # Read the scientific document in markdown format
            logger.info(f"Processing scientific document: {filename}")
            scientific_document_filepath = f"{root}/{filename}"
            scientific_document = read_text_file(scientific_document_filepath)

            # Initialize orchestrator configuration
            orchestrator_config = OrchestratorConfig(
                llm_name=llm_model,
                normalization_llm_name=normalization_llm_model,
                process_schema=process_schema,
                scientific_document=scientific_document,
                examples=examples,
                extraction_data_model=ALDProcessList,
                pubchem_lmdb_path=lmdb_pubchem_path,
                synonym_to_cid_mapping=synonym_to_cid_mapping
            )

            # Initialize the Workflow configuration
            workflow_config = WorkflowConfig(
                normalize_extracted_data=True,
                clean_extracted_data=False,
                validate_extracted_data=False
            )

            # Extract knowledge using the orchestrator agent
            final_state = orchestrate_extraction_workflow(orchestrator_config, workflow_config)
            logger.info(f"Extraction completed for document: {root}/{filename}")

            # Get the extracted knowledge from the final state
            extracted_knowledge = final_state["extracted_json"]

            # Get the normalized knowledge from the final state
            normalized_knowledge = final_state["normalized_json"]

            # Get the updated synonym to CID mapping used during normalization to save for next papers
            updated_synonym_to_cid_mapping = final_state.get("synonym_to_cid_mapping", synonym_to_cid_mapping)

            # Save the updated synonym to CID mapping back to the lookup dictionary file
            file_saved = save_json_file(os.path.dirname(pubchem_lookup_dict_path), "PubChem-Synonym-CID.json", synonym_to_cid_mapping)
            if not file_saved: raise Exception("Error saving PubChem synonym to CID mapping JSON file.")
            logger.info(f"Updated PubChem synonym to CID mapping saved to: {pubchem_lookup_dict_path}")

            # Save the extracted information to a JSON file
            file_saved = save_json_file(res_dir, json_filename, extracted_knowledge)
            if not file_saved: raise Exception(f"Failed to save extracted information for document: {filename}")
            logger.info(f"Extracted information saved to: {res_dir}/{json_filename}")

            # Save the normalized extracted information to a JSON file
            file_saved = save_json_file(norm_results_dir, json_filename, normalized_knowledge)
            if not file_saved: raise Exception(f"Failed to save normalized extracted information for document: {filename}")
            logger.info(f"Normalized extracted information saved to: {norm_results_dir}/{json_filename}")