import logging
import asyncio

from httpx import HTTPStatusError

from data.models.api.pubchem_property import PubChemPropertyResponse
from data.models.api.pubchem_synonyms import PubChemSynonymsResponse
from scikg_extract.utils.rest_client import RestClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to make GET request to PubChem API
def pubchem_get_request(base_url: str, endpoint: str, timeout: int = 10, params: dict = None):
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
    response = asyncio.run(restclient.get(endpoint, params=params))
    return response

async def main():
    """Main function to demonstrate PubChem API requests."""

    # Initialize Logger
    logger = logging.getLogger(__name__)
    logger.info("Testing PubChem API Client")
    
    # PubChem API Base URL and Timeout
    pubchem_base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    pubchem_timeout = 10

    # Initializing the RestClient
    restclient = RestClient(base_url=pubchem_base_url, timeout=pubchem_timeout)

    # Example usage: Fetch properties for a compound by CID
    try:
        cid = "3007857"  # CID for Zinc Oxide
        endpoint = f"compound/cid/{cid}/property/MolecularFormula,IUPACName,CanonicalSMILES,InChIKey/JSON"
        logger.info(f"Fetching properties for CID {cid} from PubChem on endpoint: {pubchem_base_url}/{endpoint}")
        response = await restclient.get(endpoint)
        response = PubChemPropertyResponse.model_validate(response)
        logger.info(f"Properties for CID {cid}: {response}")
    except HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
    except Exception as e:
        logger.error(f"Exception occurred: {e}")

    # Example usage: Fetch properties from a compound by name
    try:
        compound_name = "Zinc Oxide"
        endpoint = f"compound/name/{compound_name}/property/MolecularFormula,IUPACName,CanonicalSMILES,InChIKey/JSON"
        logger.info(f"Fetching properties for {compound_name} from PubChem on endpoint: {pubchem_base_url}/{endpoint}")
        response = await restclient.get(endpoint)
        response = PubChemPropertyResponse.model_validate(response)
        logger.info(f"Properties for {compound_name}: {response}")
    except HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
    except Exception as e:
        logger.error(f"Exception occurred: {e}")

    # Example usage: Fetch synonyms for a compound by name
    try:
        compound_name = "ZnO"
        endpoint = f"compound/name/{compound_name}/synonyms/JSON"
        logger.info(f"Fetching synonyms for {compound_name} from PubChem on endpoint: {pubchem_base_url}/{endpoint}")
        response = await restclient.get(endpoint)
        response = PubChemSynonymsResponse.model_validate(response)
        logger.info(f"Synonyms for {compound_name} with CID {response.InformationList.Information[0].CID}: {response.InformationList.Information[0].Synonym}")
    except HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
    except Exception as e:
        logger.error(f"Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())