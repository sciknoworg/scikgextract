"""
Evaluate BC5CDR extraction results against gold-standard test set.
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
    parser.add_argument("--include_keys", default="text,type", help="Comma-separated list of keys to include in entity evaluation (e.g., 'text,type').")
    parser.add_argument("--exclude_keys", default=None, help="Comma-separated list of keys to exclude from entity evaluation (e.g., 'subtype').")
    parser.add_argument("--relation_keys", default="type,chemical,disease", help="Comma-separated list of keys to use for relation evaluation (e.g., 'type,chemical,disease').")
    parser.add_argument("--span_f1", action="store_true", help="Whether to compute span-based Micro-F1 for entity evaluation.")
    parser.add_argument("--output", default=None, help="Path to save the evaluation results as a JSON file (e.g., 'results/evaluation_summary.json').")
    
    # Parse the command-line arguments
    args = parser.parse_args()

    # Initialize LLM model
    llm_model = args.llm_model or "claude-sonnet-4.6"

    # Initialize logging
    logger = LogHandler.setup_module_logging("scikg_extract", run_id=f"evaluate_bc5cdr_{llm_model}")
    logger.info("Starting BC5CDR evaluation script...")
    logger.info(f"Evaluating extraction results for LLM model: {llm_model}")

    # Initialize experiment name
    experiment = args.experiment or "experiment1"
    logger.info(f"Evaluating extraction results for experiment: {experiment}")

    # Initialize the output path
    output = args.output

    config = {
        "llm_model": llm_model,
        "experiment": experiment,
        "include_keys": [k.strip() for k in args.include_keys.split(",") if k.strip()],
        "exclude_keys": [k.strip() for k in args.exclude_keys.split(",") if k.strip()] if args.exclude_keys else None,
        "relation_keys": [k.strip() for k in args.relation_keys.split(",") if k.strip()],
        "span_f1": args.span_f1,
        "output": output,
    }

    run_evaluation("BC5CDR", config)
