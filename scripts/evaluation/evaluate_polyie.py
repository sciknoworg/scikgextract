"""
Evaluate PolyIE extraction results against gold-standard test set.
"""
# Python Imports
import os
import argparse

# SciKGExtract Imports
from scikg_extract.evaluation.runner import run_evaluation
from scikg_extract.utils.log_handler import LogHandler

if __name__ == "__main__":
    # Initialize the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm_model", required=False, help="The name of the LLM model used for extraction (e.g., 'gpt-4', 'gpt-3.5-turbo').")
    parser.add_argument("--experiment", help="The name of the experiment or extraction run to evaluate (e.g., 'experiment1', 'experiment2').")
    parser.add_argument("--include_categories", default="chemicalNames,propertyNames,propertyValues,conditions", help="Comma-separated list of entity categories to include in evaluation (e.g., 'chemicalNames,propertyNames').")
    parser.add_argument("--relation_keys", default="chemicalName,propertyName,propertyValue", help="Comma-separated list of keys to use for relation evaluation (e.g., 'chemicalName,propertyName,propertyValue').")
    parser.add_argument("--output", default=None, help="Path to save the evaluation results as a JSON file (e.g., 'results/evaluation_summary.json').")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Initialize LLM model
    llm_model = args.llm_model or "llama-3.3-70b-instruct"

    # Initialize logging
    logger = LogHandler.setup_module_logging("scikg_extract", run_id=f"evaluate_polyie_{llm_model}")
    logger.info("Starting PolyIE evaluation script...")
    logger.info(f"Evaluating extraction results for LLM model: {llm_model}")

    # Initialize experiment name
    experiment = args.experiment or "experiment4"
    logger.info(f"Evaluating extraction results for experiment: {experiment}")

    # Initialize the output path
    output = args.output

    # Process the include categories for entity evaluation
    include_cats = [c.strip() for c in args.include_categories.split(",") if c.strip()]
    
    config = {
        "llm_model": llm_model,
        "experiment": experiment,
        "gold_path": os.path.join("data", "gold-standard-datasets", "PolyIE", "processed", "test.json"),
        "ext_dir": os.path.join("results", "extractions", "PolyIE", experiment, "test", llm_model),
        "include_categories": [c.strip() for c in args.include_categories.split(",") if c.strip()],
        "relation_keys": [k.strip() for k in args.relation_keys.split(",") if k.strip()],
        "output": output,
    }

    run_evaluation("PolyIE", config)
