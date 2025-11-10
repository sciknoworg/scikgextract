import os
import argparse
from typing import List, Dict

import pandas as pd

from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.dict_utils import flatten_record
from scikg_extract.utils.file_utils import read_json_file

def read_data_category(filename: str, json_data: List[dict], category: str, skip_properties: List[str] = []) -> List[Dict[str, str]]:
    """
    Reads a specific data category from the JSON data and converts it to a list of rows for DataFrame construction.
    Args:
        filename (str): The source JSON filename.
        json_data (List[dict]): The extracted JSON data.
        category (str): The data category to read (e.g., "synthesis_conditions").
        skip_properties (List[str], optional): List of properties to skip. Defaults to [].
    Returns:
        List[Dict[str, str]]: A list of rows representing the data for the specified category.
    """
    
    # Initialize the logger
    logger = LogHandler.get_logger("scikg_extract.data_export.json_to_excel.read_data_category")
    logger.debug(f"Reading data category: {category} from file: {filename}")

    # Initialize list to hold rows
    rows = []

    # Iterate over multiple process entries if present
    for index, entry in enumerate(json_data):

        # Check if the category exists in the entry
        if category in entry:
            
            # Flatten the records for the category
            property_value_pairs = flatten_record(entry[category])

            # Skip if no data found
            if not property_value_pairs: continue

            # Filter out skipped properties by substring match
            property_value_pairs = [(p, v) for p, v in property_value_pairs if not any(skip_prop in p for skip_prop in skip_properties)]

            # Construct a row dictionary
            row = {}

            # Add metadata
            row["Filename"] = filename
            row["Process Number"] = index + 1

            # Add property-value pairs
            row.update({property: value for property, value in property_value_pairs})
            logger.debug(f"Extracted row for category {category}: {row}")
            
            # Append the row to the list of rows
            rows.append(row)

    # Return the list of rows for the category
    return rows

def format_rows_with_same_columns(rows: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Formats rows ensuring they all have the same columns, filling missing values with empty strings.
    Args:
        rows (List[Dict[str, str]]): The list of row dictionaries.
    Returns:
        pd.DataFrame: The formatted DataFrame with consistent columns.
    """

    # Initialize the logger
    logger = LogHandler.get_logger("scikg_extract.data_export.json_to_excel.format_rows_with_same_columns")
    logger.debug("Formatting rows to ensure consistent columns...")

    # Find distinct property names across all rows
    distinct_properties = set()
    for row in rows:
        distinct_properties.update(row.keys())
    logger.debug(f"Distinct properties found: {distinct_properties}")

    # Initialize new list for formatted rows
    formatted_rows = []

    # Format each row to have all columns
    for row in rows:
        formatted_row = {prop: row.get(prop, "") for prop in distinct_properties}
        formatted_rows.append(formatted_row)
    
    # Convert to DataFrame
    df = pd.DataFrame(formatted_rows)

    # Sort the DataFrame columns by column names
    df = df.reindex(sorted(df.columns), axis=1)

    # Index columns: Filename and Process Number first
    index_columns = ["Filename", "Process Number"]
    other_columns = [col for col in df.columns if col not in index_columns]
    df = df[index_columns + other_columns]

    # Return the formatted DataFrame
    return df

if __name__ == "__main__":

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Convert extracted JSON data to Excel format.")
    parser.add_argument("--input", type=str, required=False, help="Path to the directory containing extracted JSON files.")
    parser.add_argument("--output", type=str, required=False, help="Path to save the output Excel file.")
    parser.add_argument("--key", type=str, default="processes", help="Key containing nested JSON data to export.")
    parser.add_argument("--llm_model", type=str, default="gpt-5-mini", help="The name of the large language model used during extraction.")

    # Parse arguments
    args = parser.parse_args()

    # Initialize logger
    logger = LogHandler.setup_module_logging("scikg_extract")
    logger.info("Starting JSON to Excel conversion...")

    # Input Path
    input_path = args.input if args.input else "results/extracted-data/atomic-layer-deposition/experimental-usecase/version1/IGZO/AtomicLimits Database"
    logger.info(f"Input Path: {input_path}")

    # Output Excel Path
    output_path = args.output if args.output else "results/extracted-data/atomic-layer-deposition/experimental-usecase/version1/IGZO/AtomicLimits Database/extracted_data_IGZO_gpt5mini.xlsx"
    logger.info(f"Output Excel Path: {output_path}")

    # LLM Model used in extraction
    llm_model = args.llm_model if args.llm_model else "gpt-5-mini"
    logger.info(f"LLM Model used: {llm_model}")

    # Initialize list containing properties to skip
    skip_properties = ["quantityValue.unit.hasQuantityKind", "quantityValue.unit.sameAs", "quantityKind"]

    # Different data categories to export
    data_categories = ["aldSystem", "reactantSelection", "processParameters", "materialProperties", "deviceProperties", "otherAspects"]

    # Initialize dictionary to hold row dictionaries for each category
    category_rows = {}

    # Iterate over JSON files in the input directory
    for root, _, files in os.walk(input_path):
        
        # Skipping if no files found
        if not files: continue

        # Extracting LLM model from directory structure
        llm = root.split(os.sep)[-1]
        if llm != llm_model: continue

        # Iterate over files
        for file in files:

            # Process only JSON files
            if not file.endswith(".json"): continue

            # Read the JSON file
            file_path = os.path.join(root, file)
            json_data = read_json_file(file_path)
            json_data = json_data.get(args.key, json_data) if args.key else json_data
            logger.info(f"Processing file: {file_path} with {len(json_data)} entries.")

            # Iterate over data categories
            for category in data_categories:
                
                # Read data for the category
                rows = read_data_category(file, json_data, category, skip_properties)
                
                # Skip if no rows found for the category
                if not rows: continue

                # Initialize category in dictionary if not present
                if category not in category_rows:
                    category_rows[category] = []

                # Append rows to the category
                category_rows[category].extend(rows)

    # Format rows for each category to ensure consistent columns
    for category in data_categories:

        # Skip if no rows for the category
        if category not in category_rows or not category_rows[category]: continue

        # Format rows with same columns
        category_rows[category] = format_rows_with_same_columns(category_rows[category])

    # Write to Excel with multiple sheets
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        
        # Iterate over categories and write each to a separate sheet
        for category in data_categories:

            # Skip if no rows for the category
            if category not in category_rows or category_rows[category].empty: continue

            # Write DataFrame to Excel sheet
            sheet_name = category[:31]  # Excel sheet name limit
            category_rows[category].to_excel(writer, sheet_name=sheet_name, index=False)
            logger.info(f"Wrote category '{category}' to sheet '{sheet_name}' with {len(category_rows[category])} rows.")

