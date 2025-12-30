import json

from scikg_extract.utils.json_utils import validate_json_instance
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.agents.states import ExtractionState

def json_validator(state: ExtractionState) -> ExtractionState:
    """
    Validates JSON data against a predefined schema.
    Args:
        state (ExtractionState): The current state of the extraction process containing the JSON data to be validated.
    Returns:
        ExtractionState: The updated state with the validation results.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info("Starting JSON validation tool...")

    # Extract schema and instance from the state
    schema = state.process_schema
    instance = state.extracted_json
    logger.debug(f"Schema for validation: {json.dumps(schema)}")
    logger.debug(f"Instance to validate: {json.dumps(instance)}")

    # Get the key containing nested JSON objects to validate
    process_instances_key = state.process_instances_key

    # Extract the list of process instances
    process_instances = instance.get(process_instances_key, [])
    logger.debug(f"Extracted {len(process_instances)} process instances for validation.")

    # Validate each process instance
    valid_json = True
    for index, process_instance in enumerate(process_instances):
        logger.debug(f"Validating process instance {index + 1}")
        
        # Validate the process instance
        is_valid = validate_json_instance(process_instance, schema)
        logger.debug(f"Instance Validation Result: {is_valid}")

        # Update valid_json flag
        valid_json = valid_json and is_valid
    
    # Update the state with the validation result
    state.extraction_json_valid = valid_json

    # Return the state
    return state