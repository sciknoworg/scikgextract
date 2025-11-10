import os
import json
import argparse

from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.agents.extraction_agent import extract_knowledge
from scikg_extract.utils.file_utils import read_json_file, read_text_file, save_json_file
from data.models.schema.ALD_experimental_schema import ALDProcessList

if __name__ == "__main__":

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Extract structured ALD process information from scientific documents.")
    parser.add_argument("--llm_model", type=str, help="The name of the large language model to use.")
    parser.add_argument("--process_name", type=str, default="Atomic Layer Deposition", help="The name of the scientific process.")
    parser.add_argument("--process_description", type=str, default="A thin film deposition technique that involves the sequential use of a gas phase chemical process.", help="A brief description of the scientific process.")
    parser.add_argument("--results_dir", type=str, help="Directory to save the extracted data.")
    parser.add_argument("--process_schema", type=str, help="Path to the process schema JSON file.")
    parser.add_argument("--process_examples", type=str, help="Path to the gold-standard examples text file.")
    parser.add_argument("--scientific_docs_dir", type=str, help="Directory containing scientific documents in text/markdown format.")
    parser.add_argument("--pubchem_lmdb_path", type=str, help="Path to the PubChem LMDB database for normalization.")
    parser.add_argument("--pubchem_cid_mapping_path", type=str, help="Path to the PubChem CID mapping file.")

    # Parse the arguments
    args = parser.parse_args()

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("scikg_extract")
    logger.info("Starting ALD information extraction script...")

    # Initialize the LLM model
    llm_model = args.llm_model if args.llm_model else "gpt-5-mini"
    logger.debug(f"Using LLM model: {llm_model}")

    # Initalize the process details
    process_name = args.process_name if args.process_name else "Atomic Layer Deposition"
    process_description = args.process_description if args.process_description else "A thin film deposition technique that involves the sequential use of a gas phase chemical process."
    logger.debug(f"Process Name: {process_name}")
    logger.debug(f"Process Description: {process_description}")

    # Results directory
    results_dir = args.results_dir if args.results_dir else "results/extracted-data/atomic-layer-deposition/experimental-usecase/version1/IGZO/Extra"
    results_dir = f"{results_dir}/{llm_model}"
    logger.debug(f"Results Directory: {results_dir}")

    # Create results directory if it doesn't exist
    os.makedirs(results_dir, exist_ok=True)

    # Read the process schema from a JSON file
    process_schema_path = args.process_schema if args.process_schema else "data/schemas/ALD-experimental/ALD-experimental-schema.json"
    process_schema = read_json_file(process_schema_path)
    logger.debug(f"Process Schema: {process_schema}")

    # Read the gold-standard examples from a text file
    examples_path = args.process_examples if args.process_examples else "data/examples/Atomic-layer-deposition/IGZO/example1.txt"
    examples = read_text_file(examples_path)
    logger.debug(f"Process Examples: \n{examples}")

    # Directory containing scientific documents
    scientific_docs_dir = args.scientific_docs_dir if args.scientific_docs_dir else "data/research-papers/Atomic-layer-deposition/markdown/IGZO/Extra"
    logger.debug(f"Scientific Documents Directory: {scientific_docs_dir}")

    # PubChem LMDB path
    pubchem_lmdb_path = args.pubchem_lmdb_path if args.pubchem_lmdb_path else "data/external/pubchem/pubchem_cid_lmdb"

    # Load manual curated PubChem CID mapping lookup dictionary
    pubchem_lookup_dict_path = args.pubchem_cid_mapping_path if args.pubchem_cid_mapping_path else "data/resources/PubChem-Synonym-CID.json"
    synonym_to_cid_mapping = read_json_file(pubchem_lookup_dict_path)
    logger.info(f"Loaded PubChem CID mapping lookup dictionary with {len(synonym_to_cid_mapping)} entries from: {pubchem_lookup_dict_path}")

    # Process each scientific document in the specified directory
    for filename in os.listdir(scientific_docs_dir):
        
        # Process only markdown or text files
        if not filename.endswith(".md") and not filename.endswith(".txt"): 
            logger.debug(f"Skipping non-markdown/text file: {filename}")
            continue

        # Log the file being processed
        logger.info(f"Processing scientific document: {filename}")

        # Read the scientific document in markdown format
        scientific_document_filepath = f"{scientific_docs_dir}/{filename}"
        scientific_document = read_text_file(scientific_document_filepath)

        # Extract structured knowledge using the extraction agent
        extracted_info = extract_knowledge(llm_model, process_name, process_description, process_schema, scientific_document, examples, ALDProcessList, pubchem_lmdb_path, synonym_to_cid_mapping)
        logger.debug(f"Extracted Information from {filename}: {extracted_info}")
        logger.info(f"Extraction completed for document: {scientific_docs_dir}/{filename}")

        # Save the extracted information to a JSON file
        json_filename = f"{os.path.splitext(filename)[0]}.json"
        file_saved = save_json_file(results_dir, json_filename, extracted_info)
        if not file_saved: raise Exception(f"Failed to save extracted information for document: {filename}")
        logger.info(f"Extracted information saved to: {results_dir}/{json_filename}")