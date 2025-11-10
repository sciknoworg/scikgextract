import os
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import load_json_input

def is_primitive(val: Any) -> bool:
    """
    Check if a value is a primitive type (str, int, float, bool, None).
    Args:
        val (Any): The value to check.
    Returns:
        bool: True if the value is a primitive type, otherwise False.
    """
    return isinstance(val, (str, int, float, bool)) or val is None

def parse_number(val: Any) -> Optional[float]:
    """
    Parse a value as a float, handling common formats like percentages and commas.
    Args:
        val (Any): The value to parse.
    Returns:
        Optional[float]: The parsed float value, or None if parsing fails.
    """
    # Attempt to parse a value as a float, handling common formats like percentages and commas.
    if isinstance(val, (int, float)):
        return float(val)
    
    # Handle strings that may represent numbers
    if isinstance(val, str):
        # Strip whitespace
        s = val.strip()

        # Handle percentages
        if s.endswith("%"):
            return float(s[:-1].replace(",", "").strip()) / 100.0
        
        # Remove commas and try to convert to float
        s2 = s.replace(",", "")
        try:
            return float(s2)
        except ValueError:
            return None
    
    # If not a number or string, return None
    return None

def samples_from_document(obj: Any) -> List[Dict]:
    """
    Extract samples from a loaded JSON document.
    Args:
        obj (Any): The loaded JSON document (could be a dict or list).
    Returns:
        List[Dict]: A list of samples (dictionaries) extracted from the document.
    """
    # Extract samples from the loaded JSON document.
    samples: List[Dict] = []

    # If the document is a list of dicts, treat each dict as a sample
    if isinstance(obj, list):
        samples = [el for el in obj if isinstance(el, dict)]
    # If the document is a single dict, treat it as one sample
    elif isinstance(obj, dict):
        samples.append(obj)
    
    # Return the list of samples
    return samples

def flatten_record(rec: Any, prefix: str = "") -> List[Tuple[str, Any]]:
    """
    Flatten a nested record (dicts/lists) into (property_path, value) pairs.
    Args:
        rec (Any): The record to flatten (could be a dict, list, or primitive).
        prefix (str): The prefix for property paths (used in recursion).
    Returns:
        List[Tuple[str, Any]]: A list of (property_path, value) pairs.
    """
    # Initialize output list
    out: List[Tuple[str, Any]] = []
    
    # Flatten a nested record (dicts/lists) into (property_path, value) pairs.
    if is_primitive(rec):
        out.append((prefix.rstrip(".") or "(root)", rec)) 
        return out

    # Handle dicts
    if isinstance(rec, dict):
        for k, v in rec.items():
            new_prefix = f"{prefix}{k}"
            if is_primitive(v):
                out.append((new_prefix, v))
            else:
                out.extend(flatten_record(v, new_prefix + "."))
        return out

    # Handle lists
    if isinstance(rec, list):
        if not rec:
            return out
        if all(is_primitive(x) for x in rec):
            for v in rec:
                out.append((prefix.rstrip(".") or "(root)", v))
            return out
        for idx, item in enumerate(rec):
            out.extend(flatten_record(item, f"{prefix}[{idx}]."))
        return out
    
    # Return empty if not handled
    return out

def compute_stats_for_folder(input_dir: str, skip_keys: List[str] = [], key: str = None) -> pd.DataFrame:
    """
    Compute data statistics from extracted JSON files in a specified directory.
    Args:
        input_dir (str): The directory containing the JSON files.
        skip_keys (List[str]): List of properties which has to be skipped if found in the property path.
        key (str): If specified, only process nested JSON objects under this key.
    Returns:
        pd.DataFrame: A DataFrame containing the computed statistics.
    """

    # Initialize the logger
    logger = LogHandler.get_logger("scikg_extract")
    logger.info(f"Computing data statistics for folder: {input_dir}")

    # Stats accumulators
    papers_with_property: Dict[str, Set[str]] = defaultdict(set)
    occurrences: Dict[str, int] = defaultdict(int)
    distinct_strings: Dict[str, Set[str]] = defaultdict(set)
    numeric_values: Dict[str, List[float]] = defaultdict(list)

    # Process each JSON file in the input directory
    for root, _, filenames in os.walk(input_dir):

        # Skipping if no files in the directory
        if not filenames: continue

        # Iterate over each file
        logger.info(f"Total files found in {root}: {len(filenames)}")
        for fname in filenames:
            
            # Only process JSON files
            if not fname.lower().endswith(".json"): continue
            logger.info(f"Processing file: {fname}")

            # Read and parse the JSON file
            doc = load_json_input(Path(os.path.join(root, fname)))

            # If a specific key is provided, extract that part of the JSON
            if key is not None and isinstance(doc, dict):
                doc = doc.get(key, {})

            # Extract samples from the document
            samples = samples_from_document(doc)
            if not samples: continue
            logger.info(f"Found {len(samples)} samples in file: {fname}")

            # Intialize set to track properties seen in this file
            props_seen_in_file: Set[str] = set()

            # Process each sample in the file
            for sample in samples:
                for prop_path, raw_val in flatten_record(sample, prefix=""):
                    
                    # Skip empty values
                    if raw_val is None or (isinstance(raw_val, str) and raw_val.strip() == ""):
                        continue

                    # Skip specified keys
                    if any(skip_key in prop_path for skip_key in skip_keys):
                        continue
                    
                    # Update occurrences and papers_with_property
                    occurrences[prop_path] += 1
                    props_seen_in_file.add(prop_path)

                    # Numeric parsing
                    parsed_num = parse_number(raw_val)

                    # Store values based on type
                    if parsed_num is not None:
                        numeric_values[prop_path].append(parsed_num)
                    else:
                        # Treat as string-like
                        if isinstance(raw_val, bool):
                            # Booleans we record in strings set as "true"/"false"
                            distinct_strings[prop_path].add(str(raw_val))
                        else:
                            # String / other -> convert to string and add to set
                            distinct_strings[prop_path].add(str(raw_val))

            # Update papers_with_property using the set found in this file
            for p in props_seen_in_file:
                papers_with_property[p].add(fname)

    # build summary
    rows = []
    for prop in sorted(set(list(occurrences.keys()) + list(distinct_strings.keys()) + list(numeric_values.keys()))):
        num_papers = len(papers_with_property.get(prop, set()))
        occ = occurrences.get(prop, 0)
        distinct_count = len(distinct_strings.get(prop, set()))
        distinct_sample_list = sorted(list(distinct_strings.get(prop, set()))) if distinct_count > 0 else []
        nums = numeric_values.get(prop, [])
        min_v = float(min(nums)) if nums else None
        max_v = float(max(nums)) if nums else None

        # Create the summary row
        rows.append(
            {
                "property": prop,
                "papers_with_value": num_papers,
                "total_occurrences": occ,
                "distinct_values_count": distinct_count,
                "distinct_values_sample": distinct_sample_list,
                "min_value": min_v,
                "max_value": max_v,
            }
        )

    # Return as DataFrame
    return pd.DataFrame(rows)
 
if __name__ == "__main__":

    # Initialize argument parser
    parser = argparse.ArgumentParser(description="Compute data statistics from extracted JSON files.")
    parser.add_argument("--input_dir", type=str, required=False, help="Input directory containing JSON files.")
    parser.add_argument("--output_csv", type=str, required=False, help="Output CSV file path for statistics.")
    parser.add_argument("--skip_keys", type=str, nargs='*', default=[], help="List of properties to skip.")
    parser.add_argument("--key", type=str, default="processes", help="Key containing nested JSON objects to validate")

    # Parse the arguments
    args = parser.parse_args()

    # Configure the logger
    logger = LogHandler.setup_module_logging("scikg_extract")
    logger.info("Starting computing data statistics...")

    # Input directory containing JSON files
    input_dir = args.input_dir if args.input_dir else "results/extracted-data/atomic-layer-deposition/experimental-usecase/version1/IGZO/Extra/gpt-5-mini"
    logger.info(f"Input directory: {input_dir}")

    # Output CSV file path
    out_csv = args.output_csv if args.output_csv else "results/statistics/atomic-layer-deposition/experimental-usecase/version1/IGZO/Extra/gpt-5-mini"
    logger.info(f"Output CSV path: {out_csv}")

    # Create output directory if it doesn't exist
    os.makedirs(out_csv, exist_ok=True)

    # Output statistics CSV file path
    out_csv = f"{out_csv}/data_statistics.csv"
    logger.info(f"Final output CSV path: {out_csv}")

    # Skip keys containing these substrings
    skip_keys = args.skip_keys if args.skip_keys else ["quantityKind", "unit.sameAs", "unit.hasQuantityKind"]
    logger.info(f"Skipping keys: {skip_keys}")

    # Compute statistics for the folder
    df = compute_stats_for_folder(input_dir, skip_keys, key=args.key)

    # Print a concise table preview
    pd.set_option("display.max_rows", None)

    # Save the statistics to a CSV file
    df.to_csv(out_csv, index=False)
    logger.info(f"Data statistics saved to CSV at: {out_csv}")
    logger.info("Data statistics computation completed.")