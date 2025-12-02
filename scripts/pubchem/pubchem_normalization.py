import sys
import asyncio
import argparse

import lmdb
from httpx import HTTPStatusError
from rapidfuzz import fuzz

from data.models.api.pubchem_synonyms import PubChemSynonymsResponse

from scikg_extract.services.pubchem_cid_mapping import open_env_for_read, lookup_by_synonym
from scikg_extract.utils.rest_client import RestClient
from scikg_extract.config.normalization.normalizationConfig import NormalizationConfig
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.dict_utils import get_value_by_path, set_value_by_path
from scikg_extract.utils.file_utils import read_json_file, save_json_file
from scikg_extract.utils.string_utils import normalize_string

def pubchem_get_request(base_url: str, endpoint: str, timeout: int = 10, params: dict = None) -> dict:
    """
    Makes a GET request to the specified PubChem API endpoint and returns the JSON response.
    Args:
        base_url (str): The base URL for the PubChem API.
        endpoint (str): The specific API endpoint to query.
        timeout (int, optional): The timeout for the request in seconds. Defaults to 10.
    Returns:
        dict: The JSON response from the PubChem API.
    Raises:
        httpx.HTTPError: If an error occurs during the request.
    """

    # Initialize the Logger
    logger = LogHandler.get_logger("pubchem_normalization.pubchem_get_request")
    logger.debug(f"Making PubChem GET request to endpoint: {base_url}/{endpoint} with params: {params}")

    # Initialize the RestClient
    restclient = RestClient(base_url=base_url, timeout=timeout)
    
    # Make the GET request asynchronously
    response = asyncio.run(restclient.get(endpoint, params=params))
    logger.debug(f"Received response from PubChem API: {response}")
    
    # Return the JSON response
    return response

def fetch_cid_from_pubchem_api(pubchem_base_url: str, pubchem_endpoint: str, pubchem_timeout: int, value: str) -> list[str] | None:
    """
    Fetches PubChem CIDs for a given chemical name using the PubChem API.
    Args:
        pubchem_base_url (str): The base URL for the PubChem API.
        pubchem_endpoint (str): The specific API endpoint to query.
        pubchem_timeout (int): The timeout for the request in seconds.
        value (str): The chemical name to look up.
    Returns:
        list[str] | None: A list of PubChem CIDs or None if not found.
    """

    # Initialize the logger
    logger = LogHandler.get_logger("pubchem_normalization.fetch_cid_from_pubchem_api")
    logger.debug(f"Fetching CIDs for {value} from PubChem using endpoint: {pubchem_base_url}/{pubchem_endpoint}")

    try:
        # Make the GET request to PubChem API
        response = pubchem_get_request(pubchem_base_url, pubchem_endpoint, timeout=pubchem_timeout)
        
        # Parse the response to Pydantic model
        response = PubChemSynonymsResponse.model_validate(response)
        logger.debug(f"Parsed PubChem response for {value}: {response}")
        
        # Extract CIDs from the response
        cids = [info.CID for info in response.InformationList.Information]

        # Create normalized PubChem URIs
        normalized_uris = [f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" for cid in cids]
        logger.debug(f"Normalized URIs for {value}: {normalized_uris}")
        
        # Return the normalized URIs
        return normalized_uris
    except HTTPStatusError as e:
        logger.debug(f"HTTP error occurred: {e}")
    except Exception as e:
        logger.debug(f"Exception occurred while normalizing value {value} using the name endpoint: {e}")

def normalize_with_lookup_dict(synonym_to_cid_mapping: dict[str, str], value: str) -> list | None:
    """
    Normalize a chemical name using a synonym to PubChem CID mapping created while normalizing earlier values.
    Args:
        synonym_to_cid_mapping (dict[str, str]): A dictionary mapping synonyms to PubChem CIDs.
        value (str): The chemical name to normalize.
    Returns:
        list | None: A list of normalized URIs or None if not found.
    """

    # Initialize the logger
    logger = LogHandler.get_logger("pubchem_normalization.normalize_with_lookup_dict")
    logger.debug(f"Normalizing value: {value} using Lookup CID mapping...")

    # Initialize list to hold normalized URIs
    normalized_uris = []

    # Check if the value exists in the synonym to CID mapping
    cid = synonym_to_cid_mapping.get(value, "")

    # Check using fuzzy matching if exact match not found
    if not cid:
        logger.debug(f"No exact match found for {value} in lookup dict. Attempting fuzzy matching...")
        for syn, c in synonym_to_cid_mapping.items():
            score = fuzz.ratio(value, syn.lower())
            if score >= 85:
                cid = f"{cid},{c}" if cid else c

    # If not found, return None
    if not cid: return None

    # If found, create normalized URIs
    normalized_uris.extend([f"https://pubchem.ncbi.nlm.nih.gov/compound/{c.strip()}" for c in cid.split(",")])
    logger.debug(f"Normalized URIs for {value} from lookup dict: {normalized_uris}")

    # Return the list of normalized URIs
    return normalized_uris

def normalize_value_with_pubchem_api(value: str) -> list | None:
    """
    Normalizes a chemical name using PubChem API to retrieve its CID and properties.
    Args:
        value (str): The chemical name to normalize.
    Returns:
        list | None: A list of normalized URIs or None if not found.
    """

    # Initialize the logger
    logger = LogHandler.get_logger("pubchem_normalization.normalize_value_with_pubchem_api")
    logger.debug(f"Normalizing value: {value} using PubChem API...")

    # PubChem API Base URL and Timeout
    pubchem_base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    pubchem_timeout = 10

    # Initialize list to hold normalized URIs
    normalized_uris = []

    # Step 1: Fetching CID and Synonyms for the value using the name endpoint
    endpoint = f"compound/name/{value}/synonyms/JSON"
    cids = fetch_cid_from_pubchem_api(pubchem_base_url, endpoint, pubchem_timeout, value)
    normalized_uris.extend(cids if cids else [])

    # Step 2: Fetching CID and Synonyms for the value using the molecular formula endpoint
    endpoint = f"compound/fastformula/{value}/synonyms/JSON"
    cids = fetch_cid_from_pubchem_api(pubchem_base_url, endpoint, pubchem_timeout, value)
    normalized_uris.extend(cids if cids else [])

    # Remove duplicates URIs
    normalized_uris = list(set(normalized_uris))
    logger.debug(f"Final normalized URIs for {value} using PubChem API: {normalized_uris}")

    # Return the list of normalized URIs or None if empty
    return normalized_uris if normalized_uris else None

def normalize_value_with_pubchem_cid_mapping(env: lmdb.Environment, value: str) -> list | None:
    """
    Normalize a chemical name using a predefined PubChem CID to synonym mapping.
    Args:
        env (lmdb.Environment): The LMDB environment containing the CID mapping.
        value (str): The chemical name to normalize.
    Returns:
        list | None: A list of normalized URIs or None if not found.
    """

    # Initialize the logger
    logger = LogHandler.get_logger("pubchem_normalization.normalize_value_with_pubchem_cid_mapping")
    logger.debug(f"Normalizing value: {value} using PubChem CID mapping...")

    # Lookup CIDs by synonym in the LMDB database
    matching_cids = lookup_by_synonym(env, value)

    # If no matching CIDs found, return None
    if not matching_cids: 
        logger.debug(f"No matching CIDs found for value: {value} in LMDB PubChem CID mapping.")
        return None
    
    # Create normalized URIs from the matching CIDs
    normalized_uris = [f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" for _, _, cid in matching_cids]
    logger.debug(f"Normalized URIs for {value} from LMDB CID mapping: {normalized_uris}")

    # Return the list of normalized URIs
    return normalized_uris

def update_process_json_with_normalized_value(data: dict, full_path: str, value: str, normalized_uris: list) -> None:
    """
    Updates the process JSON data at the specified path with the normalized URIs.
    Args:
        data (dict): The extracted process JSON data.
        full_path (str): The dot-notation path to the property to update.
        value (str): The original value being normalized.
        normalized_uris (list): The list of normalized URIs to set at the specified path.
    """

    # Initialize the logger
    logger = LogHandler.get_logger("pubchem_normalization.update_process_json_with_normalized_value")
    logger.debug(f"Updating JSON at path: {full_path} with normalized URIs: {normalized_uris}")

    # Format the normalized URIs as a dictionary containing the original value and normalized URIs
    normalized_value = {"value": value, "sameAs": normalized_uris}

    # Set the normalized value at the specified path in the JSON data
    success = set_value_by_path(data, full_path, normalized_value)
    if not success: raise Exception(f"Error updating JSON data at path: {full_path} with normalized URIs: {normalized_uris}")
    logger.debug(f"Successfully updated JSON data at path: {full_path} with normalized URIs.")

def normalize_process_json(data: dict, lmdb_env: lmdb.Environment, properties_to_normalize: list, properties_to_exclude: list, synonym_to_cid_mapping: dict[str, str] = {}) -> None:
    """
    Normalizes specified properties in the process JSON data using PubChem CIDs.
    Args:
        data (dict): The extracted process JSON data.
        lmdb_env (lmdb.Environment): The LMDB environment for PubChem CID mapping.
        properties_to_normalize (list): List of dot-notation paths to properties to normalize.
        properties_to_exclude (list): List of dot-notation paths to properties to exclude from normalization.
        synonym_to_cid_mapping (dict[str, str], optional): A dictionary mapping synonyms to PubChem CIDs. Defaults to {}.
    """

    # Initialize the logger
    logger = LogHandler.get_logger("pubchem_normalization.normalize_process_json")
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

            # Normalize the value with CIDs lookup dictionary if provided
            normalized_uris = normalize_with_lookup_dict(synonym_to_cid_mapping, value)

            if normalized_uris:
                logger.debug(f"Path: {full_path}, Original Value: {value}, Normalized URIs from lookup dict: {normalized_uris}")
                update_process_json_with_normalized_value(data, full_path, original_value, normalized_uris)
                logger.debug(f"Updated JSON data at path: {full_path} with normalized URIs from lookup dict.")
                continue

            # Normalize the value using PubChem API
            normalized_uris = normalize_value_with_pubchem_api(value)
            if normalized_uris:
                logger.debug(f"Path: {full_path}, Original Value: {value}, Normalized URIs: {normalized_uris}")
                update_process_json_with_normalized_value(data, full_path, original_value, normalized_uris)
                logger.debug(f"Updated JSON data at path: {full_path} with normalized URIs from PubChem API.")
                continue

            # Normalize the value using PubChem CID mapping LMDB
            normalized_uris = normalize_value_with_pubchem_cid_mapping(lmdb_env, value)
            if normalized_uris:
                logger.debug(f"Path: {full_path}, Original Value: {value}, Normalized URIs from LMDB: {normalized_uris}")
                update_process_json_with_normalized_value(data, full_path, original_value, normalized_uris)
                logger.debug(f"Updated JSON data at path: {full_path} with normalized URIs from LMDB.")

if __name__ == "__main__":

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Normalize values with PubChem CIDs from extracted Process JSON data.")
    parser.add_argument("--input_json", type=str, help="Path to the extracted process JSON file.")
    parser.add_argument("--output_json", type=str, help="Path to save the normalized JSON file.")
    parser.add_argument("--key", type=str, default="processes", help="Key containing nested JSON data to normalize")
    parser.add_argument("--lmdb_pubchem_path", type=str, help="Path to the LMDB PubChem CID mapping database.")
    parser.add_argument("--pubchem_lookup_dict_path", type=str, help="Path to the manual curated PubChem CID mapping lookup dictionary JSON file.")

    # Parse arguments
    args = parser.parse_args()

    # Initialize logger
    logger = LogHandler.setup_module_logging("pubchem_normalization")
    logger.info("Starting PubChem normalization...")

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
    input_json = args.input_json if args.input_json else "results/extracted-data/atomic-layer-deposition/experimental-usecase/version1/ZnO/ZnEt2 - H2O/gpt-5-mini/2 Lujala et al.json"
    logger.info(f"Input JSON file: {input_json}")

    # Output JSON file path
    output_json = args.output_json if args.output_json else "results/extracted-data/atomic-layer-deposition/experimental-usecase/version3/ZnO/ZnEt2 - H2O/gpt-5-mini"
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
        logger.info(f"Normalizing process {index + 1}/{len(data)}...")
        normalize_process_json(process, env, properties_to_normalize, properties_to_exclude, synonym_to_cid_mapping)
        logger.info(f"Completed normalization for process {index + 1}/{len(data)}.")
    
    # Save the normalized JSON data to output file
    filename = f"{output_json.split("/")[-1]}.json"
    output_path = "/".join(output_json.split("/")[:-1])
    file_saved = save_json_file(output_path, filename, data)
    if not file_saved: raise Exception("Error saving normalized JSON file.")
    logger.info(f"Normalized JSON data saved to: {output_json}")