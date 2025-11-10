from jsonschema import Draft7Validator

from scikg_extract.utils.log_handler import LogHandler

def json_schema_validate(schema: dict) -> bool:
    """
    Validate the provided JSON schema using Draft7Validator.
    Args:
        schema (dict): The JSON schema to validate.
    Returns:
        bool: True if the schema is valid, False otherwise.
    """
    
    # Initialize the logger
    logger = LogHandler.get_logger(__name__)

    try:
        Draft7Validator.check_schema(schema)
        return True
    except Exception as e:
        logger.debug(f"Schema validation error: {e}")
        return False
    
def validate_json_instance(instance: dict, schema: dict) -> bool:
    """
    Validate a JSON instance against the provided JSON schema.
    Args:
        instance (dict): The JSON instance to validate.
        schema (dict): The JSON schema to validate against.
    Returns:
        bool: True if the instance is valid, False otherwise.
    """
    # Initialize the logger
    logger = LogHandler.get_logger(__name__)

    try:
        validator = Draft7Validator(schema)
        return validator.validate(instance)
    except Exception as e:
        logger.debug(f"Instance validation error: {e}")
        return False