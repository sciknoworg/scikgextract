import asyncio

from httpx import HTTPStatusError

from data.models.api.pubchem_property import PubChemPropertyResponse
from data.models.api.pubchem_synonyms import PubChemSynonymsResponse

from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.rest_client import RestClient

async def pubchem_get_request(base_url: str, endpoint: str, timeout: int = 10, params: dict = None):
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
    restclient = RestClient(base_url=base_url, timeout=timeout)
    response = await restclient.get(endpoint, params=params)
    return response

async def fetch_compound_by_cid(cid: str, properties: list[str], base_url: str, timeout: int = 10) -> PubChemPropertyResponse:
    """
    Fetches compound properties from PubChem by CID.
    Args:
        cid (str): The PubChem Compound ID.
        properties (list[str]): List of properties to fetch.
        base_url (str): The base URL for the PubChem API.
        timeout (int, optional): The timeout for the request in seconds. Defaults to 10.
    Returns:
        PubChemPropertyResponse: The response model containing compound properties.
    Raises:
        httpx.HTTPError: If an error occurs during the request.
    """
    # Initialize Logger
    logger = LogHandler.get_logger("pubchem_api.fetch_compound_by_cid")
    logger.info(f"Fetching properties for CID {cid} from PubChem with properties: {properties}")

    try:
        endpoint = f"compound/cid/{cid}/property/{','.join(properties)}/JSON"
        response_json = await pubchem_get_request(base_url, endpoint, timeout)
        response_model = PubChemPropertyResponse.model_validate(response_json)
        return response_model
    except HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching CID {cid}: {e}")
    except Exception as e:
        logger.error(f"Exception occurred while fetching CID {cid}: {e}")

async def fetch_compound_by_name(name: str, properties: list[str], base_url: str, timeout: int = 10) -> PubChemPropertyResponse:
    """
    Fetches compound properties from PubChem by compound name.
    Args:
        name (str): The compound name.
        properties (list[str]): List of properties to fetch.
        base_url (str): The base URL for the PubChem API.
        timeout (int, optional): The timeout for the request in seconds. Defaults to 10.
    Returns:
        PubChemPropertyResponse: The response model containing compound properties.
    Raises:
        httpx.HTTPError: If an error occurs during the request.
    """
    # Initialize Logger
    logger = LogHandler.get_logger("pubchem_api.fetch_compound_by_name")
    logger.info(f"Fetching properties for compound name '{name}' from PubChem with properties: {properties}")

    try:
        endpoint = f"compound/name/{name}/property/{','.join(properties)}/JSON"
        response_json = await pubchem_get_request(base_url, endpoint, timeout)
        response_model = PubChemPropertyResponse.model_validate(response_json)
        return response_model
    except HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching compound '{name}': {e}")
    except Exception as e:
        logger.error(f"Exception occurred while fetching compound '{name}': {e}")

async def fetch_synonyms_by_name(name: str, base_url: str, timeout: int = 10) -> PubChemSynonymsResponse:
    """
    Fetches compound synonyms from PubChem by compound name.
    Args:
        name (str): The compound name.
        base_url (str): The base URL for the PubChem API.
        timeout (int, optional): The timeout for the request in seconds. Defaults to 10.
    Returns:
        PubChemSynonymsResponse: The response model containing compound synonyms.
    Raises:
        httpx.HTTPError: If an error occurs during the request.
    """
    # Initialize Logger
    logger = LogHandler.get_logger("pubchem_api.fetch_synonyms_by_name")
    logger.info(f"Fetching synonyms for compound name '{name}' from PubChem")

    try:
        endpoint = f"compound/name/{name}/synonyms/JSON"
        response_json = await pubchem_get_request(base_url, endpoint, timeout)
        response_model = PubChemSynonymsResponse.model_validate(response_json)
        return response_model
    except HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching synonyms for compound '{name}': {e}")
    except Exception as e:
        logger.error(f"Exception occurred while fetching synonyms for compound '{name}': {e}")

async def main():
    """Main function to test PubChem API client."""

    # Configure and Initialize Logger
    logger = LogHandler.setup_module_logging("pubchem_api")
    logger.info("Testing PubChem API Client...")
    
    # PubChem API Base URL and Timeout
    pubchem_base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    pubchem_timeout = 10

    # Example usage: Fetch properties for a compound by CID
    cid = "3007857"  # CID for Zinc Oxide
    response = await fetch_compound_by_cid(cid, ["MolecularFormula", "IUPACName", "CanonicalSMILES", "InChIKey"], pubchem_base_url, pubchem_timeout)
    logger.info(f"Properties for CID {cid}: \n{response}")

    # Example usage: Fetch properties from a compound by name
    compound_name = "Zinc Oxide"
    response = await fetch_compound_by_name(compound_name, ["MolecularFormula", "IUPACName", "CanonicalSMILES", "InChIKey"], pubchem_base_url, pubchem_timeout)
    logger.info(f"Properties for compound '{compound_name}': \n{response}")

    # # Example usage: Fetch synonyms for a compound by name
    compound_name = "ZnO"
    response = await fetch_synonyms_by_name(compound_name, pubchem_base_url, pubchem_timeout)
    logger.info(f"Synonyms for compound '{compound_name}': \n{response}")

if __name__ == "__main__":
    asyncio.run(main())