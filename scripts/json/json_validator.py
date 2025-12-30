import json
import logging
import argparse

from jsonschema import Draft7Validator

from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import read_json_file

def json_schema_validate(schema: dict) -> bool:
    """
    Validate the provided JSON schema using Draft7Validator.
    Args:
        schema (dict): The JSON schema to validate.
    Returns:
        bool: True if the schema is valid, False otherwise.
    """
    
    # Initialize the logger
    logger = LogHandler.get_logger("json_validator.json_schema_validate")

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
    logger = LogHandler.get_logger("json_validator.validate_json_instance")

    try:
        validator = Draft7Validator(schema)
        return validator.validate(instance)
    except Exception as e:
        logger.debug(f"Instance validation error: {e}")
        return False
    
if __name__ == "__main__":
    """Main function to validate JSON schema and instances."""

    # Add argument parser for schema and instance files
    parser = argparse.ArgumentParser(description="Validate JSON schema and instances.")
    parser.add_argument("--schema", type=str, required=False, help="Path to the JSON schema file.")
    parser.add_argument("--instance", type=str, required=False, help="Path to the JSON instance file.")
    parser.add_argument("--key", type=str, default="processes", help="Key containing nested JSON objects to validate")

    # Parse the arguments
    args = parser.parse_args()

    # Configure and Initialize the logger
    logger = LogHandler.setup_module_logging("json_validator")
    logger.info("Starting JSON schema and instance validation...")
    
    # JSON schema file path
    schema_file_path = 'data/schemas/ALD-experimental/ALD-experimental-schema.json'
    if args.schema:
        schema_file_path = args.schema
    logger.info(f'Using schema file: {schema_file_path}')

    # Instance file path
    instance_file_path = 'results/extracted-data/atomic-layer-deposition/experimental-usecase/version1/ZnO/ZnO_ALD&Temp_Kim_2011_cleaned.json'
    if args.instance:
        instance_file_path = args.instance
    logger.info(f'Using instance file: {instance_file_path}')

    # Read the JSON schema
    schema = read_json_file(schema_file_path)
    logger.debug(f'Schema content: {json.dumps(schema)}')

    # Validate the JSON schema
    is_schema_valid = json_schema_validate(schema)
    logger.info(f'Schema valid: {is_schema_valid}')

    # Read the JSON instance
    instance = read_json_file(instance_file_path)
    logger.debug(f'Instance content: {json.dumps(instance)}')

    # Check if a specific key is provided for nested validation
    instance_to_validate = instance
    if args.key and args.key in instance:
        instance_to_validate = instance.get(args.key, {})
        logger.info(f'Validating nested objects under key: {args.key}')

    # Check if the instance to validate is a list or a single object
    if not isinstance(instance_to_validate, list):
        instance_to_validate = [instance_to_validate]
        
    # Validate the JSON instance/s against the schema
    for obj in instance_to_validate:
        is_instance_valid = validate_json_instance(obj, schema)
        logger.info(f'Instance valid: {is_instance_valid}')