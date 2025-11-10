import os
import logging
import argparse

from scikg_extract.utils.dict_utils import remove_null_values
from scikg_extract.utils.file_utils import read_json_file, save_json_file
    
if __name__ == "__main__":

    # Add argument parser
    parser = argparse.ArgumentParser(description="Clean JSON files.")
    parser.add_argument("--input", type=str, required=False, help="Path to the input JSON file.")
    parser.add_argument("--output", type=str, required=False, help="Path to the output cleaned JSON file.")
    parser.add_argument("--verbose", action="store_true", default=True, help="Enable verbose")

    # Parse the arguments
    args = parser.parse_args()

    # Configure the logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Initialize the logger
    logger = logging.getLogger(__name__)
    logger.info("Starting JSON cleaning process...")

    # Input file path
    input_path = args.input if args.input else "results/extracted-data/atomic-layer-deposition/experimental-usecase/version1/ZnO/ZnO_ALD&Temp_Kim_2011.json"
    logger.info(f"Using input file: {input_path}")

    # Output file path
    output_path = args.output if args.output else "results/extracted-data/atomic-layer-deposition/experimental-usecase/version1/ZnO"
    logger.info(f"Using output file: {output_path}")

    # Read the input JSON file
    data = read_json_file(input_path)
    logger.debug(f"JSON data loaded: {data}")

    # Clean the JSON data
    cleaned_data = remove_null_values(data)
    logger.debug(f"Cleaned JSON data: {cleaned_data}")

    # Save the cleaned JSON data to the output file
    filename = f'{os.path.splitext(os.path.basename(input_path))[0]}_cleaned.json'
    file_saved = save_json_file(output_path, filename, cleaned_data)
    if file_saved: logger.info("JSON cleaning process completed successfully.")
