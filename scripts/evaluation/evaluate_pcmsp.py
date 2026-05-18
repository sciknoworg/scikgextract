"""
Evaluate PcMSP extraction results against gold-standard test set.
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
    parser.add_argument("--include_categories", default="materials,operations,descriptors,values,properties,devices,brands", help="Comma-separated list of entity categories to include in evaluation (e.g., 'materials,operations,descriptors').")
    parser.add_argument("--exclude_categories", default=None, help="Comma-separated list of entity categories to exclude from evaluation (e.g., 'brands').")
    parser.add_argument("--relation_keys", default="type,source,target", help="Comma-separated list of keys to use for relation evaluation (e.g., 'type,source,target').")
    parser.add_argument("--output", default=None, help="Path to save the evaluation results as a JSON file (e.g., 'results/evaluation_summary.json').")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Initialize LLM model
    llm_model = args.llm_model or "gpt-4o"

    # Initialize logging
    logger = LogHandler.setup_module_logging("scikg_extract", run_id=f"evaluate_pcmsp_{llm_model}")
    logger.info("Starting PcMSP evaluation script...")
    logger.info(f"Evaluating extraction results for LLM model: {llm_model}")

    # Initialize experiment name
    experiment = args.experiment or "experiment4"
    logger.info(f"Evaluating extraction results for experiment: {experiment}")

    # Initialize the output path
    output = args.output

    # Process the include and exclude categories for entity evaluation
    include_cats = [c.strip() for c in args.include_categories.split(",") if c.strip()]
    config = {
        "llm_model": llm_model,
        "experiment": experiment,
        "include_categories": [c.strip() for c in args.include_categories.split(",") if c.strip()],
        "exclude_categories": [c.strip() for c in args.exclude_categories.split(",") if c.strip()] if args.exclude_categories else None,
        "relation_keys": [k.strip() for k in args.relation_keys.split(",") if k.strip()],
        "output": output,
    }

    run_evaluation("PcMSP", config)
