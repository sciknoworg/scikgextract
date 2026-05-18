"""
Evaluate ZnO and IGZO extraction results against AtomicLimits gold-standard annotations.

Aggregation method:
 - Per-field metrics are computed using `entity_precision_recall_f1` and
     aggregated with `aggregate_metrics()`; per-field aggregates include counts
     (`tp`, `fp`, `fn`) and computed `precision`, `recall`, `f1` (micro/macro as
     produced by `aggregate_metrics`).
 - An overall micro-averaged precision/recall/F1 is produced by summing the
     per-field `tp`, `fp`, and `fn` totals across all annotated fields and
     computing precision/recall/F1 from those totals; this is attached under the
     `overall` key in the returned aggregated results.
 - BERTScore (when requested) is combined across fields using a simple
     unweighted mean of the per-field `bertscore` dictionaries (if present);
     the combined BERTScore is included in `aggregated["overall"]["bertscore"]`.
"""
# Python Imports
import os
import argparse

# SciKGExtract Imports
from scikg_extract.evaluation.runner import run_evaluation
from scikg_extract.utils.log_handler import LogHandler


if __name__ == "__main__":
    # Initialize argument parser for command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm_model", required=False, help="The name of the LLM model used for extraction (e.g., 'gpt-4', 'gpt-3.5-turbo').")
    parser.add_argument("--version", help="The version of the extraction results to evaluate (e.g., 'version1', 'version2').")
    parser.add_argument("--material", choices=["ZnO", "IGZO", "both"], help="The material to evaluate (e.g., 'ZnO', 'IGZO', or 'both').")
    parser.add_argument("--output", default=None, help="Path to save the evaluation results as a JSON file (e.g., 'results/evaluation_summary.json').")
    args = parser.parse_args()

    llm_model = args.llm_model or "gpt-4o"
    material = args.material or "IGZO"

    logger = LogHandler.setup_module_logging("scikg_extract", run_id=f"evaluate_{material}_{llm_model}")
    logger.info("Starting ZnO and IGZO evaluation script...")
    logger.info(f"Evaluating extraction results for LLM model: {llm_model}")
    logger.info(f"Evaluating extraction results for material: {material}")

    version = args.version or "version5"
    logger.info(f"Evaluating extraction results for version: {version}")

    output = args.output

    dataset = material if material != "both" else "ZnO"
    config = {
        "llm_model": llm_model,
        "version": version,
        "material": material,
        "compute_bertscore": True,
        "output": output,
    }

    run_evaluation(dataset, config)
