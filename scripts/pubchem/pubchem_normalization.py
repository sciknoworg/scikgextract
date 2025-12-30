# Python Imports
import os
import sys
import argparse

# External Imports
import lmdb

# SciKG_Extract Service Imports
from scikg_extract.services.pubchem_cid_mapping import open_env_for_read

# SciKG_Extract Config Imports
from scikg_extract.config.normalization.normalizationConfig import NormalizationConfig

# SciKG_Extract Tools Imports
from scikg_extract.tools.extraction.pubchem_normalization import normalize_value_with_pubchem_api
from scikg_extract.tools.extraction.pubchem_normalization import normalize_with_lookup_dict
from scikg_extract.tools.extraction.pubchem_normalization import normalize_value_with_pubchem_cid_mapping
from scikg_extract.tools.extraction.pubchem_normalization import perform_llm_disambiguation
from scikg_extract.tools.extraction.pubchem_normalization import update_process_json_with_normalized_value

# SciKG_Extract Utils Imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.dict_utils import get_value_by_path
from scikg_extract.utils.file_utils import read_json_file, save_json_file
from scikg_extract.utils.string_utils import normalize_string

def update_synonym_to_cid_mapping(synonym_to_cid_mapping: dict[str, str], value: str, cids: list[str]) -> dict[str, str]:
    """
    Updates the synonym to CID mapping dictionary with new entries.
    Args:
        synonym_to_cid_mapping (dict[str, str]): The existing synonym to CID mapping dictionary.
        value (str): The synonym value.
        cids (list[str]): The list of PubChem CIDs corresponding to the synonym.
    Returns:
        dict[str, str]: The updated synonym to CID mapping dictionary.
    """
    
    # Create comma-separated string of CIDs
    cid_string = ",".join([cid.split("/")[-1] for cid in cids])

    # Update the mapping dictionary
    if value.lower() not in synonym_to_cid_mapping or value not in synonym_to_cid_mapping:
        synonym_to_cid_mapping[value] = cid_string

    # Return the updated mapping dictionary
    return synonym_to_cid_mapping

def run_normalizers(value: str, lmdb_env: lmdb.Environment, synonym_to_cid_mapping: dict[str, str] = {}) -> list[str]:
    """
    Runs normalizers (Manual Created synonym CID Lookup, PubChem API and PubChem dump Lookup) to obtain PubChem CIDs for a given value.
    Args:
        value (str): The value to normalize.
        lmdb_env (lmdb.Environment): The LMDB environment for PubChem CID mapping.
        synonym_to_cid_mapping (dict[str, str], optional): A dictionary mapping synonyms to PubChem CIDs. Defaults to {}.
    Returns:
        list[str]: A list of normalized PubChem CID URIs.
    """

    # Normalize the value with CIDs lookup dictionary if provided
    normalized_uris = normalize_with_lookup_dict(synonym_to_cid_mapping, value)
    if normalized_uris: return normalized_uris

    # Normalize the value using PubChem API
    normalized_uris = normalize_value_with_pubchem_api(value)
    if normalized_uris: return normalized_uris

    # Normalize the value using PubChem CID mapping LMDB
    normalized_uris = normalize_value_with_pubchem_cid_mapping(lmdb_env, value)
    if normalized_uris: return normalized_uris

    # If no normalization found, return empty list
    return []

def normalize_process_json(data: dict, lmdb_env: lmdb.Environment, properties_to_normalize: list, properties_to_exclude: list, synonym_to_cid_mapping: dict[str, str] = {}) -> dict[str, str]:
    """
    Normalizes specified properties in the process JSON data using PubChem CIDs.
    Args:
        data (dict): The extracted process JSON data.
        lmdb_env (lmdb.Environment): The LMDB environment for PubChem CID mapping.
        properties_to_normalize (list): List of dot-notation paths to properties to normalize.
        properties_to_exclude (list): List of dot-notation paths to properties to exclude from normalization.
        synonym_to_cid_mapping (dict[str, str], optional): A dictionary mapping synonyms to PubChem CIDs. Defaults to {}.
    Returns:
        dict[str, str]: New synonym to CID mapping found during normalization.
    """

    # Initialize the logger
    logger = LogHandler.get_logger("scikg_extract.normalize_process_json")
    logger.debug("Starting normalization of process JSON data...")

    # Normalize each specified property
    for path in properties_to_normalize:

        # Skip excluded properties
        if path in properties_to_exclude:
            logger.debug(f"Skipping excluded property path: {path}")
            continue
        
        # Get all values for the specified path
        values_with_paths = get_value_by_path(data, path)
        logger.debug(f"Retrieved values for path {path}: {values_with_paths}")

        # Normalize each value found at the specified path
        for value, full_path in values_with_paths:
            logger.debug(f"Normalizing value at path {full_path}: {value}")

            # Copy of the original value
            original_value = value

            # Clean value with string normalization
            value = normalize_string(value)
            logger.debug(f"Normalized string value: {value}")

            # Execute normalizers to get normalized URIs
            normalized_uris = run_normalizers(value, lmdb_env, synonym_to_cid_mapping)

            if normalized_uris:
                logger.debug(f"Path: {full_path}, Original Value: {value}, Normalized URIs: {normalized_uris}")
                update_process_json_with_normalized_value(data, full_path, original_value, normalized_uris)
                synonym_to_cid_mapping = update_synonym_to_cid_mapping(synonym_to_cid_mapping, original_value, normalized_uris)
                logger.debug(f"Updated JSON data at path: {full_path} with normalized URIs")
                continue

            # Normalize the value using LLM disambiguation
            disambiguted_details = perform_llm_disambiguation([value], "gpt-5")
            logger.debug(f"LLM Disambiguation result for value {value}: {disambiguted_details}")

            # Excecute the normalizers again on the disambiguated name/molecular formaula
            if disambiguted_details and disambiguted_details.Molecular_Formula:
                normalized_uris = run_normalizers(disambiguted_details.Molecular_Formula, lmdb_env, synonym_to_cid_mapping)

                if normalized_uris:
                    logger.debug(f"Path: {full_path}, Original Value: {value}, Normalized URIs after LLM disambiguation: {normalized_uris}")
                    update_process_json_with_normalized_value(data, full_path, original_value, normalized_uris)
                    synonym_to_cid_mapping = update_synonym_to_cid_mapping(synonym_to_cid_mapping, original_value, normalized_uris)
                    logger.debug(f"Updated JSON data at path: {full_path} with normalized URIs after LLM disambiguation")
                    continue

            # If NO normalization found, update the value with empty SameAs list
            if not normalized_uris:
                logger.debug(f"No normalization found for value: {value} at path: {full_path}. Updating with empty SameAs list.")
                update_process_json_with_normalized_value(data, full_path, original_value, [])

    # Return the updated synonym to CID mapping
    logger.debug("Completed normalization of process JSON data.")
    return synonym_to_cid_mapping

if __name__ == "__main__":

    # Configure argument parser
    parser = argparse.ArgumentParser(description="Normalize values with PubChem CIDs from extracted Process JSON data.")
    parser.add_argument("--input_json", type=str, help="Path to the extracted process JSON file.")
    parser.add_argument("--output_json", type=str, help="Path to save the normalized JSON file.")
    parser.add_argument("--key", type=str, default="processes", help="Key containing nested JSON data to normalize")
    parser.add_argument("--lmdb_pubchem_path", type=str, help="Path to the LMDB PubChem CID mapping database.")
    parser.add_argument("--pubchem_lookup_dict_path", type=str, help="Path to the manual curated PubChem CID mapping lookup dictionary JSON file.")

    # Parse arguments
    args = parser.parse_args()

    # Initialize logger
    logger = LogHandler.setup_module_logging("scikg_extract")
    logger.info("Starting PubChem normalization procedure...")

    # Load manual curated PubChem CID mapping lookup dictionary
    pubchem_lookup_dict_path = args.pubchem_lookup_dict_path if args.pubchem_lookup_dict_path else "data/resources/PubChem-Synonym-CID.json"
    synonym_to_cid_mapping = read_json_file(pubchem_lookup_dict_path)
    logger.info(f"Loaded PubChem CID mapping lookup dictionary with {len(synonym_to_cid_mapping)} entries from: {pubchem_lookup_dict_path}")

    # Read the properties to normalize
    properties_to_normalize = NormalizationConfig.include_paths
    if not properties_to_normalize:
        logger.warning("No properties specified for normalization. Exiting.")
        sys.exit(0)
    logger.info(f"Total properties to normalize: {len(properties_to_normalize)}, Properties: {properties_to_normalize}")

    # Read the properties to exclude
    properties_to_exclude = NormalizationConfig.exclude_paths
    logger.info(f"Total properties to exclude from normalization: {len(properties_to_exclude)}, Properties: {properties_to_exclude}")

    # Input JSON file path
    input_json = args.input_json if args.input_json else "results/extracted-data/ALD/version2/ZnO-IGZO-papers/experimental-usecase/ZnO/ZnEt2 - H2O/gpt-4o/2 Lujala et al.json"
    logger.info(f"Input JSON file: {input_json}")

    # Extract Input JSON file name with extension
    input_filename = input_json.split("/")[-1]
    logger.debug(f"Input JSON file name: {input_filename}")

    # Output JSON file path
    output_json = args.output_json if args.output_json else "results/extracted-data/ALD/version5/ZnO-IGZO-papers/experimental-usecase/ZnO/ZnEt2 - H2O/gpt-4o"
    logger.info(f"Output JSON file: {output_json}")

    # Open LMDB PubChem CID mapping environment
    lmdb_pubchem_path = args.lmdb_pubchem_path if args.lmdb_pubchem_path else "data/external/pubchem/pubchem_cid_lmdb"
    env = open_env_for_read(lmdb_pubchem_path, readonly=True)
    logger.info(f"Opened LMDB PubChem CID mapping environment from: {lmdb_pubchem_path}")

    # Read the input JSON data
    data = read_json_file(input_json)
    data = data.get(args.key, data) if args.key else data
    logger.info(f"Total processes in input data: {len(data)}")

    # Normalize the process JSON data
    for index, process in enumerate(data):
        # Normalize the process JSON data
        logger.info(f"Normalizing process {index + 1}/{len(data)}...")
        synonym_to_cid_mapping = normalize_process_json(process, env, properties_to_normalize, properties_to_exclude, synonym_to_cid_mapping)
        logger.info(f"Completed normalization for process {index + 1}/{len(data)}.")

        # Sort the synonym to CID mapping dictionary by keys
        synonym_to_cid_mapping = dict(sorted(synonym_to_cid_mapping.items()))

        # Save the updated synonym to CID mapping file
        file_saved = save_json_file(os.path.dirname(pubchem_lookup_dict_path), "PubChem-Synonym-CID.json", synonym_to_cid_mapping)
        if not file_saved: raise Exception("Error saving PubChem synonym to CID mapping JSON file.")
        logger.info(f"Updated PubChem synonym to CID mapping saved to: {pubchem_lookup_dict_path}")
    
    # Save the normalized JSON data to output file
    file_saved = save_json_file(output_json, input_filename, data)
    if not file_saved: raise Exception("Error saving normalized JSON file.")
    logger.info(f"Normalized JSON data saved to: {output_json}")