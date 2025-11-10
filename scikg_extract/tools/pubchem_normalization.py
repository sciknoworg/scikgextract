import sys
import asyncio
import argparse

import lmdb
from httpx import HTTPStatusError
from rapidfuzz import fuzz

from data.models.api.pubchem_synonyms import PubChemSynonymsResponse

from scikg_extract.services.pubchem_cid_mapping import open_env_for_read, lookup_by_synonym
from scikg_extract.utils.rest_client import RestClient
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.dict_utils import get_value_by_path, set_value_by_path
from scikg_extract.utils.string_utils import normalize_string
from scikg_extract.agents.states import ExtractionState

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

def pubchem_normalization(state: ExtractionState) -> ExtractionState:
    """
    Normalizes chemical names in the extracted JSON data using PubChem.
    Args:
        state (ExtractionState): The current state of the extraction process containing the JSON data to be normalized.
    Returns:
        ExtractionState: The updated state with the normalized JSON data.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting PubChem normalization tool...")

    # Open LMDB environment for PubChem CID mapping
    lmdb_env = open_env_for_read(state["pubchem_lmdb_path"], readonly=True)

    # Iterate over each process in the extracted JSON data
    extracted_data = state["extracted_json"]

    for process in extracted_data.get("processes", []):
        
        # Get the process JSON data
        data = process

        # Normalize each specified property
        for path in state["normalization_properties_to_include"]:

            # Skip excluded properties
            if path in state["normalization_properties_to_exclude"]:
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
                normalized_uris = normalize_with_lookup_dict(state["synonym_to_cid_mapping"], value)

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

    # For demonstration, we will just log that normalization is complete
    logger.info("PubChem normalization completed.")

    # Return the state unchanged (replace with actual normalized data in practice)
    return state