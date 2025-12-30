"""
JSON cleaning script to remove all null, Not Found, and empty values from JSON files.
"""
# Python imports
import os
import argparse

# Scikg_Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.dict_utils import remove_null_values, remove_empty_qudt_structures
from scikg_extract.utils.file_utils import read_json_file, save_json_file
    
if __name__ == "__main__":
    """Main function to clean JSON files by removing null and empty values."""

    # Add argument parser
    parser = argparse.ArgumentParser(description="Clean JSON files.")
    parser.add_argument("--input", type=str, required=False, help="Path to the input JSON file.")
    parser.add_argument("--output", type=str, required=False, help="Path to the output cleaned JSON file.")

    # Parse the arguments
    args = parser.parse_args()

    # Configure and Initialize the logger
    logger = LogHandler.setup_module_logging("scikg_extract")
    logger.info("Starting JSON cleaning process...")

    # Input file path
    input_path = args.input if args.input else "results/extracted-data-test/ALD/version2/ZnO-IGZO-papers/experimental-usecase/IGZO/AtomicLimits Database/In(PrNMe2)Me2-GaMe3-ZnEt2-O2 plasma/gpt-5-mini/1 Sheng et al.json"
    logger.info(f"Using input file: {input_path}")

    # Output file path
    output_path = args.output if args.output else "results/extracted-data-test/ALD/version2/ZnO-IGZO-papers/experimental-usecase/IGZO/AtomicLimits Database/In(PrNMe2)Me2-GaMe3-ZnEt2-O2 plasma/gpt-5-mini"
    logger.info(f"Using output file: {output_path}")

    # Read the input JSON file
    data = read_json_file(input_path)
    logger.debug(f"JSON data loaded: {data}")

    # Remove EMPTY QUDT structures
    cleaned_data = remove_empty_qudt_structures(data)
    logger.debug(f"JSON data after removing empty QUDT structures: {cleaned_data}")

    # Skip keys that should not be cleaned
    skip_keys = ["sameAs"]

    # Clean the JSON data by removing null and empty values
    cleaned_data = remove_null_values(cleaned_data, skip_keys=skip_keys)
    logger.debug(f"Cleaned JSON data: {cleaned_data}")

    # Save the cleaned JSON data to the output file
    filename = f'{os.path.splitext(os.path.basename(input_path))[0]}_cleaned.json'
    file_saved = save_json_file(output_path, filename, cleaned_data)
    if file_saved: logger.info("JSON cleaning process completed successfully.")
