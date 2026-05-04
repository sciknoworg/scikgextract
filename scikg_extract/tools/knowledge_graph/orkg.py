"""
ORKG (Open Research Knowledge Graph) connector utilities for SciKGExtract.

Provides functions to create and validate connections to an ORKG instance, as well as to materialize templates within ORKG. These utilities are used by the Orchestrator Agent to interface with the ORKG platform for storing and managing extracted structured knowledge.
"""
# External Imports
from orkg import ORKG

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# Scikg_Extract Agent Imports
from scikg_extract.agents.states import ExtractionState

def get_orkg_connector(host: str, email: str, password: str) -> ORKG:
    """
    Creates and returns an ORKG connector instance using the provided credentials.
    Args:
        host (str): The ORKG host URL.
        email (str): The email address for authentication.
        password (str): The password for authentication.
    Returns:
        ORKG: An instance of the ORKG connector.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Creating ORKG connector...")

    # Create ORKG connector instance
    orkg_connector = ORKG(host=host, creds=(email, password))
    logger.info("ORKG connector created successfully.")
    return orkg_connector

def validate_orkg_connection(orkg_connector: ORKG) -> bool:
    """
    Validates the connection to the ORKG instance using the provided credentials.
    Args:
        orkg_connector (ORKG): An instance of the ORKG connector.
    Returns:
        bool: True if the connection is successful, False otherwise.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Validating connection to ORKG...")

    # Test the connection
    valid_connection = orkg_connector.ping()
    if not valid_connection:
        raise ConnectionError("Failed to connect to ORKG with the provided credentials.")
    
    # Log successful connection
    logger.info("Successfully connected to ORKG.")
    return True

def materialize_template(orkg_connector: ORKG, template_id: str) -> bool:
    """
    Materializes a template in the ORKG instance using the provided ORKG connector.
    Args:
        orkg_connector (ORKG): An instance of the ORKG connector.
        template_id (str): The ID of the template assigned in ORKG.
    Returns:
        bool: True if the template is materialized successfully, False otherwise.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info(f"Materializing template with ID: {template_id}...")

    # Materialize the template
    template_materialized = orkg_connector.templates.materialize_template(template_id)
    if not template_materialized:
        raise RuntimeError(f"Failed to materialize template with ID: {template_id}.")
    
    # Log successful materialization
    logger.info(f"Template with ID: {template_id} materialized successfully.")
    return True