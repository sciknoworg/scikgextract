"""
JSON Cleaner Tool for SciKGExtract.

This module defines a JSON cleaning tool that is used within the SciKGExtract workflow to clean the extracted JSON data by removing null values. It operates on the ExtractionState, which is threaded through the LangGraph workflow, and updates the state with the cleaned JSON data for downstream processing.
"""
# SciKGExtract Utility Imports
from scikg_extract.utils.log_handler import LogHandler

# SciKGExtract Agents State Imports
from scikg_extract.agents.states import ExtractionState

# SciKGExtract Utility Imports
from scikg_extract.utils.dict_utils import remove_null_values, remove_empty_qudt_structures

def json_cleaner(state: ExtractionState) -> ExtractionState:
    """
    Cleans JSON data by removing null values.
    Args:
        state (ExtractionState): The current state of the extraction process containing the JSON data to be cleaned.
    Returns:
        ExtractionState: The updated state with the cleaned JSON data.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting JSON cleaning tool...")

    # Step 1: Remove all NULL values
    cleaned_data = remove_null_values(state.extracted_json)
    logger.debug(f"Cleaned JSON data after removing NULL values: {cleaned_data}")

    # # Step 2: Remove empty QUDT structures
    # cleaned_data = remove_empty_qudt_structures(cleaned_data)
    # if cleaned_data is None:
    #     cleaned_data = {}
    # logger.debug(f"Cleaned JSON data after removing empty QUDT structures: {cleaned_data}")

    # Update the state with the cleaned JSON
    state.extracted_json = cleaned_data

    # Return the updated state with cleaned JSON
    return state