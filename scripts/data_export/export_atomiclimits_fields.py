"""
Export selected fields from AtomicLimits extraction JSON files into a flat JSON and Excel/CSV. Supports flexible key selection (including wildcards), list handling, and metadata extraction from file paths. Useful for analyzing LLM performance on specific fields or for creating structured datasets from the extracted information.
"""
# Python Imports
from __future__ import annotations

import os
import argparse
import json
import re
from typing import Any, Dict, List

# Pandas Import
import pandas as pd

# SciKGExtract Imports
from scikg_extract.utils.file_utils import read_json_file, save_json_file
from scikg_extract.utils.dict_utils import flatten_record, get_value_by_path
from scikg_extract.utils.log_handler import LogHandler

def extract_meta_from_path(file_path: str, input_root: str) -> Dict[str, str]:
    """
    Return material, process_condition and model inferred from file path relative to input_root. Assumes path structure like {input_root}/{material}/{process_condition}/{model}/extracted.json, but is defensive to handle variations in depth and missing segments.
    Args:
        file_path: The full path to the JSON file being processed.
        input_root: The root input directory that is being processed, used to compute relative path.
    Returns:
        Dict[str, str]: A dictionary containing the extracted metadata fields: "material", "process_condition", and "model". If any of these cannot be inferred from the path, they will be returned as empty strings.
    """
    rel = os.path.relpath(os.path.dirname(file_path), input_root)
    parts = rel.split(os.sep)
    material = parts[0] if len(parts) >= 1 else ""
    process_condition = parts[-2] if len(parts) >= 2 else ""
    model = parts[-1] if len(parts) >= 3 else (parts[-1] if parts else "")
    
    # Defensive fallback: if path ends directly in model folder (common case), model already set
    return {"material": material, "process_condition": process_condition, "model": model}

def value_to_primitive(val: Any) -> str:
    """
    Convert a value to a primitive string representation. If the value is None, return an empty string. If the value is already a primitive type (str, int, float, bool), return it as a string. For dicts and lists, attempt to convert to a compact JSON string; if that fails, fall back to a simple string conversion.
    Args:
        val: The value to convert, which can be of any type.
    Returns:
        str: A string representation of the value.
    """
    # If value is None, return empty string
    if val is None: return ""

    # If value is already a primitive type, return as string
    if isinstance(val, (str, int, float, bool)): return str(val)
    
    # For dict/list produce compact JSON
    try:
        return json.dumps(val, ensure_ascii=False)
    except Exception:
        return str(val)

def build_row_for_process(proc: dict, meta: dict, list_sep: str) -> Dict[str, Any]:
    """
    Build a flat dictionary representing a single process record, including metadata and flattened process fields. List-valued fields are joined using the specified separator. The keys in the output dictionary are derived from the paths of the fields in the original nested structure, with metadata fields taking precedence to avoid overwriting.
    Args:
        proc: The original nested dictionary representing the process record extracted from the JSON file.
        meta: A dictionary containing metadata fields extracted from the file path (e.g., material, process_condition, model).
        list_sep: A string separator used to join list-valued fields into a single string representation.
    Returns:
        Dict[str, Any]: A flat dictionary where keys are derived from the paths of the original nested fields (with metadata fields included) and values are the corresponding primitive values or joined strings for lists.
    """
    # Initialize the dictionary for the output row
    row: Dict[str, Any] = {}

    # Add metadata fields to the row (material, process_condition, model, source_file, file_basename, process_index)
    row.update({"source_file": meta.get("source_file", ""),
                "model": meta.get("model", ""),
                "material": meta.get("material", ""),
                "process_condition": meta.get("process_condition", ""),
                "file_basename": meta.get("file_basename", ""),
                "process_index": meta.get("process_index", "")})

    # Flatten entire process record into dot notation paths and values
    pairs = flatten_record(proc)
    
    # Iterate through the flattened paths and values to build the output row
    for path, value in pairs:
        
        # Normalize path: remove trailing dots and leading '(root)'
        col = path if path != "(root)" else "process"
        
        # Avoid overwriting existing metadata columns
        if col in row:
            col = f"process.{col}"
        
        # If duplicate property names appear, combine values using list_sep
        if col in row and row[col]:
            row[col] = f"{row[col]}{list_sep}{value_to_primitive(value)}"
        else:
            row[col] = value_to_primitive(value)
    
    # Return the constructed row dictionary for the current process
    return row

def write_outputs(rows: List[Dict[str, Any]], output_json: str = None, output_excel: str = None) -> None:
    """
    Write the output rows to JSON and/or Excel files based on the specified output paths. If an output path is not provided for a format, that format will be skipped.
    Args:
        rows: A list of dictionaries, where each dictionary represents a row of data to be written to the output files.
        output_json: The file path for the output JSON file. If None, the JSON output will be skipped.
        output_excel: The file path for the output Excel file. If None, the Excel output will be skipped.
    """
    # Initialize logger
    logger = LogHandler.get_logger("export_atomiclimits_fields")

    # Write the output rows to JSON if an output path is specified
    if output_json:

        # Extract directory and filename from the output path
        dirname = os.path.dirname(output_json)
        filename = os.path.basename(output_json)

        # Ensure the output filename ends with .json
        if not filename.endswith(".json"):
            raise ValueError(f"Output JSON file name must end with .json: {filename}")
        
        # Save the JSON file
        save_json_file(dirname, filename, rows)
        logger.info(f"Wrote JSON output to {output_json} ({len(rows)} rows)")

    # Write the output rows to Excel if an output path is specified
    if output_excel:
        
        # Convert rows to DataFrame
        df = pd.DataFrame(rows)

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_excel), exist_ok=True)
        
        # Write to Excel
        df.to_excel(output_excel, index=False)
        logger.info(f"Wrote Excel file to {output_excel}")

def collect_files(input_dir: str) -> List[str]:
    """
    Recursively collect all JSON files under the input directory.
    Args:
        input_dir: Root directory to search for JSON files.
    Returns:
        List[str]: List of file paths to JSON files found under the input directory.
    """
    files: List[str] = []
    for root, _, filenames in os.walk(input_dir):
        for fname in filenames:
            if fname.lower().endswith('.json'):
                files.append(os.path.join(root, fname))
    return files

if __name__ == "__main__":
    """
    Main function to export all fields from AtomicLimits extraction JSON files into a flat JSON and Excel/CSV.
    """
    # Initialize Argument Parser
    parser = argparse.ArgumentParser(description="Export AtomicLimits fields to JSON/Excel/CSV")
    parser.add_argument("--input_dir", type=str, help="Root folder with ALD version extractions")
    parser.add_argument("--llm_model", type=str, default=None, help="Model folder name to filter (e.g. qwen3-235b-a22b).")
    parser.add_argument("--output_json", type=str, default=None, help="Output JSON file path (list of rows)")
    parser.add_argument("--output_excel", type=str, default=None, help="Output Excel file path (.xlsx). If omitted, no Excel produced")
    parser.add_argument("--list_sep", type=str, default="|", help="Separator for list values when not exploding")

    # Parse arguments
    args = parser.parse_args()

    # Initialize Logger
    logger = LogHandler.setup_module_logging("export_atomiclimits_fields")
    logger.info("Starting AtomicLimits export...")

    # Collect files to process
    input_dir = args.input_dir or "results/extractions/AtomicLimits Database/ALD/version1"
    files = collect_files(input_dir)
    logger.info(f"Found {len(files)} JSON files under {input_dir}")

    # Initialize the LLM model
    llm_model = args.llm_model or "qwen3-30b-a3b-instruct-2507"
    logger.info(f"Filtering for LLM model: {llm_model}")

    # Initialize list to hold output rows
    rows: List[Dict[str, Any]] = []

    # Process each file
    for fp in files:
        try:
            # Extract metadata from file path (material, process_condition, model)
            meta = extract_meta_from_path(fp, input_dir)
            meta.update({"source_file": os.path.relpath(fp, input_dir), "file_basename": os.path.basename(fp)})

            # filter by model specified
            model_folder = meta.get("model", "")
            if llm_model and model_folder != llm_model: continue

            # Read JSON and extract processes
            data = read_json_file(fp)
            processes = data.get("processes", []) if isinstance(data, dict) else []

            # For each process, build a row for the output based on requested keys and metadata
            for idx, proc in enumerate(processes):

                # Create a copy of meta for this process
                meta_proc = dict(meta)

                # Add process index to meta for potential use in keys or output
                meta_proc["process_index"] = idx

                # Build the output row for this process
                row = build_row_for_process(proc, meta_proc, args.list_sep)

                # Append the row to the list of rows to be output
                rows.append(row)
        except Exception as e:
            logger.exception(f"Failed processing file {fp}: {e}")

    # Write outputs to specified formats
    os.makedirs("results/exports", exist_ok=True)
    output_json = args.output_json or os.path.join("results", "exports", "AtomicLimits Database", f"{llm_model}_export.json")
    output_excel = args.output_excel or os.path.join("results", "exports", "AtomicLimits Database", f"{llm_model}_export.xlsx")

    # Write the collected rows to the specified output formats (JSON, Excel, CSV fallback)
    write_outputs(rows, output_json=output_json, output_excel=output_excel)
    logger.info("Export completed.")