# Python Imports
import os
from typing import Tuple

# SciKGExtract Config Imports
from scikg_extract.config.normalization.normalizationConfig import NormalizationConfig

# SciKGExtract Utilities Imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import read_json_file, save_json_file
from scikg_extract.utils.dict_utils import set_value_by_path, get_value_by_path

def add_puchem_cids(data: dict, property_path: str, value: str, cids: list[str]) -> Tuple[dict, bool]:
    """
    Adds PubChem CIDs to the data dictionary for a given property value.
    Args:
        data (dict): The extracted and normalized data.
        property_path (str): The path to the property in the extracted data.
        value (str): The property value to which the CIDs correspond.
        cids (list[str]): List of PubChem CIDs to add.
    Returns:
        Tuple[dict, bool]: The updated data dictionary with added PubChem CIDs and a boolean indicating if the value was found.
    """

    # Initialize the logger
    logger = LogHandler.get_logger(__name__)
    logger.info(f"Adding PubChem CIDs for value: {value}")

    # Retrieve all the entries at the specified property path
    entries = get_value_by_path(data, property_path)

    # Boolean to check if value was found
    value_found = False

    # Iterate over each entry to find matching values
    for entry, path in entries:
        # Skip if the value does not match
        if not entry.get("value") == value: continue

        # Add/Update the PubChem CIDs to the 'sameAs' field
        sameAs = entry.get("sameAs", [])
        sameAs.extend(cids)
        sameAs = list(set(sameAs))

        # Update the entry with the new 'sameAs' values
        entry["sameAs"] = sameAs
        
        # Set the updated entry back to the data dictionary
        updated = set_value_by_path(data, path, entry)
        if not updated: logger.warning(f"Failed to update entry at path: {path}")

        # Mark that the value was found and updated
        value_found = True

    # Return the updated data dictionary
    logger.info(f"Completed adding PubChem CIDs for value: {value}")
    return (data, value_found)


if __name__ == "__main__":
    
    # Initialize the logger
    logger = LogHandler.setup_module_logging("scikg_extract")
    logger.info("Starting normalization correction script...")

    # Path containing the extracted and normalized data
    extracted_data_dir = "results/extracted-data-test/ALD/version4/ZnO-IGZO-papers/experimental-usecase/IGZO"

    # Property paths to be corrected
    property_paths = NormalizationConfig.include_paths

    # Values whose PubChem CIDs has to be corrected
    target_values = ["Pd"]

    # CIDs to be added for each target value
    target_cids = ["23938"]

    # Append prefix to each target CIDs
    target_cids = [f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" for cid in target_cids]

    # Iterate over each extracted data file in the directory
    for root, _, files in os.walk(extracted_data_dir):
        
        # Skip if no files found
        if not files: continue
        logger.info(f"Processing files in directory: {root}")

        # Iterate over each file
        for file in files:
            # Construct the full file path
            file_path = os.path.join(root, file)
            logger.debug(f"Processing file: {file_path}")

            # Read the extracted and normalized data
            data = read_json_file(file_path)
            
            # Boolean to track if any process was updated
            process_updated = False

            # Iterate over each process
            for process in data.get("processes", []):
                
                # Iterate over each target value to be corrected
                for value in target_values:

                    # Iterate over each property path to be corrected
                    for property_path in property_paths:

                        # Add PubChem CIDs for the target value
                        process, updated = add_puchem_cids(process, property_path, value, target_cids)

                        # Update the process_updated flag
                        process_updated = process_updated or updated

            # Skip saving if no updates were made
            if not process_updated: continue
            
            # Save the updated data back to the file
            file_saved = save_json_file(root, file, data)
            if not file_saved:
                logger.error(f"Failed to save updated data to file: {file_path}")
            logger.info(f"Successfully updated and saved file: {file_path}")