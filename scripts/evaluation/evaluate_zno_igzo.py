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

# SciKGExtract Evaluation Imports
from scikg_extract.evaluation.metrics import entity_precision_recall_f1, aggregate_metrics, save_evaluation_results, print_evaluation_summary

# SciKGExtract Utility Imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import read_json_file, save_json_file

def parse_atomiclimits_annotation(folder_name, material) -> dict:
    """
    Parse the folder name from AtomicLimits dataset to extract the gold-standard annotation for the given material. The folder names in the AtomicLimits dataset encode the process conditions, which can be used to derive the expected precursor and co-reactants for the ALD processes. This function takes the folder name and material as input and returns a structured annotation dictionary that can be used for evaluation against the extracted results.
    Args:
        folder_name: The name of the folder in the AtomicLimits dataset, which encodes the process conditions (e.g., "ZnMe2 - O2 plasma").
        material: The material being evaluated (e.g., "ZnO" or "IGZO"), which can help determine the expected annotation structure.
    Returns:
        dict: A dictionary containing the gold-standard annotation for the specified material, including fields such as "material_deposited", "precursor", "coreactant1", "coreactant2", and "coreactant3" based on the information encoded in the folder name.
    """
    # Split the folder name by " - " to extract precursor and co-reactants
    segments = folder_name.split(" - ")

    # For IGZO, first three segments are typically precursors (e.g., "In", "Ga", "Zn"), and the last segment is the co-reactant (e.g., "O2 plasma"). For ZnO, the first segment is the precursor and the second segment is the co-reactant.
    if material == "IGZO":
        annotation = {
            "material_deposited": material,
            "precursor1": segments[0] if len(segments) > 0 else "",
            "precursor2": segments[1] if len(segments) > 1 else "",
            "precursor3": segments[2] if len(segments) > 2 else "",
            "coreactant": segments[3] if len(segments) > 3 else "",
        }
    else:
        annotation = {
            "material_deposited": material,
            "precursor": segments[0] if len(segments) > 0 else "",
            "coreactant1": segments[1] if len(segments) > 1 else "",
            "coreactant2": segments[2] if len(segments) > 2 else "",
            "coreactant3": segments[3] if len(segments) > 3 else "",
        }

    # Return the structured annotation dictionary
    return annotation

def evaluate(base_dir, llm_model, material, compute_bertscore=False, bertscore_model=None, bertscore_revision=None, results=None) -> dict:
    """
    Evaluate the extracted results for ZnO or IGZO against the gold-standard annotations derived from the folder names in the AtomicLimits dataset.
    Args:
        base_dir: The base directory where the extraction results are stored, which should contain subdirectories for each material and process condition.
        llm_model: The name of the LLM model used for extraction, which is part of the path to the processed extraction results.
        material: The material being evaluated (e.g., "ZnO" or "IGZO"), which determines the expected annotation structure and the subdirectory to look into.
        compute_bertscore: A boolean flag indicating whether to compute BERTScore for the evaluation, which can provide a more nuanced similarity measure between the predicted and gold values.
        bertscore_model: The name of the BERT model to use for computing BERTScore (e.g., "allenai/scibert_scivocab_uncased"), which should be compatible with the domain of the text being evaluated.
        bertscore_revision: The specific revision or commit hash of the BERT model to use for computing BERTScore, which can ensure reproducibility of the evaluation results.
        results: An optional dictionary to store the evaluation metrics for each field, which can be passed in to accumulate results across multiple evaluations or initialized within the function if not provided.
    Returns:
        dict: A dictionary containing the aggregated evaluation metrics for each field (e.g., "material_deposited", "precursor", "coreactant1", etc.) based on the comparison between the extracted results and the gold-standard annotations.
    """
    # Initialize logger
    logger = LogHandler.get_logger("scikg_extract")

    # If results dictionary is not provided, initialize it with empty lists for each field to store the evaluation metrics
    if not results:
        results = {"material_deposited": [], "precursor": [], "coreactant1": [], "coreactant2": [], "coreactant3": []}

    # Construct the path to the material directory based on the specified material argument
    mat_dir = os.path.join(base_dir, material)
    
    # If IGZO, append "AtomicLimits Database" to the path since IGZO results are stored in a subdirectory, while ZnO results are directly under the material directory
    atomic_db_dir = os.path.join(mat_dir, "AtomicLimits Database", "cross-evaluation") if material == "IGZO" else os.path.join(mat_dir, "cross-evaluation")
    
    # Iterate through each process condition folder
    for proc_cond in os.listdir(atomic_db_dir):
        
        # Construct the path to the processed extraction results for the current process condition and LLM model
        proc_path = os.path.join(atomic_db_dir, proc_cond, llm_model)
        if not os.path.isdir(proc_path): continue
        
        # Iterate through each extracted result file in the processed directory
        for fname in os.listdir(proc_path):
            
            # Only consider JSON files
            if not fname.endswith(".json"): continue
            logger.info(f"Evaluating process condition: {proc_cond} with extraction file: {fname}")

            # Read the predicted extraction results and parse the gold-standard annotation for the current process condition and material
            pred = read_json_file(os.path.join(proc_path, fname))
            annotation = parse_atomiclimits_annotation(proc_cond, material)
            
            # Compare each field
            for field in results:
                
                # Extract the gold value for the current field
                gold = [{"value": annotation[field]}]
                if not gold[0]["value"]: continue
                
                # Iterate over each predicted process
                for entry in pred.get("processes", []):
                    
                    # Extract the predicted material deposited
                    if field == "material_deposited":
                        pred_val = entry.get("aldSystem", {}).get("materialDeposited", "")
                        logger.debug(f"Comparing gold value: {gold} with predicted value: {pred_val} for field: {field}")

                        # Compute precision, recall, and F1 for the current field and append the metrics to the results
                        metrics = entity_precision_recall_f1(gold, [{"value": pred_val}] if pred_val else [], ["value"], compute_bertscore=compute_bertscore, bert_embedding_model=bertscore_model, bert_embedding_model_revision=bertscore_revision)

                        # Append the computed metrics to the results dictionary for the current field
                        results[field].append(metrics)
                    
                    # Extract the predicted precursor
                    elif field.startswith("precursor"):
                        
                        # Precursors list
                        pred_val_list = entry.get("reactantSelection", {}).get("precursor", [])

                        # Iterate over and extract the precursor values
                        for idx, pred_val in enumerate(pred_val_list):
                            
                            # Format the predicted value as a list of dictionaries with "value" key for evaluation
                            pred_list = [{"value": pred_val.get("precursor", "")}] if pred_val else []
                            logger.debug(f"Comparing gold value: {gold} with predicted value: {pred_list} for field: {field}")

                            # Compute precision, recall, and F1 for the current field and append the metrics to the results
                            metrics = entity_precision_recall_f1(gold, pred_list, ["value"], compute_bertscore=compute_bertscore, bert_embedding_model=bertscore_model, bert_embedding_model_revision=bertscore_revision)

                            # Append the computed metrics to the results dictionary for the current field
                            results[field].append(metrics)

                    # Extract the predicted co-reactant
                    elif field.startswith("coreactant"):
                        
                        # Co-reactants list
                        pred_val_list = entry.get("reactantSelection", {}).get("coReactant", [])

                        # Iterate over and extract the co-reactant values
                        for idx, pred_val in enumerate(pred_val_list):
                            
                            # Format the predicted value as a list of dictionaries with "value" key for evaluation
                            pred_list = [{"value": pred_val.get("coReactant", "")}] if pred_val else []
                            logger.debug(f"Comparing gold value: {gold} with predicted value: {pred_list} for field: {field}")

                            # Compute precision, recall, and F1 for the current field and append the metrics to the results
                            metrics = entity_precision_recall_f1(gold, pred_list, ["value"], compute_bertscore=compute_bertscore, bert_embedding_model=bertscore_model, bert_embedding_model_revision=bertscore_revision)

                            # Append the computed metrics to the results dictionary for the current field
                            results[field].append(metrics)
    
    # Aggregate the metrics for each field across all process conditions
    aggregated = {k: aggregate_metrics(v) for k, v in results.items()}

    # Compute an overall micro-averaged precision/recall/f1 across all fields
    total_tp = sum(m.get("tp", 0) for m in aggregated.values())
    total_fp = sum(m.get("fp", 0) for m in aggregated.values())
    total_fn = sum(m.get("fn", 0) for m in aggregated.values())
    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0

    overall = {
        "precision": overall_precision,
        "recall": overall_recall,
        "f1": overall_f1,
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
    }

    # Combine BERTScore across fields using a simple (unweighted) mean across fields that provide BERTScore.
    bs_list = [m.get("bertscore") for m in aggregated.values() if isinstance(m.get("bertscore"), dict)]
    if bs_list:
        overall["bertscore"] = {
            "precision": sum(float(b.get("precision", 0.0)) for b in bs_list) / len(bs_list),
            "recall": sum(float(b.get("recall", 0.0)) for b in bs_list) / len(bs_list),
            "f1": sum(float(b.get("f1", 0.0)) for b in bs_list) / len(bs_list),
        }

    # Attach the overall metrics to the aggregated result for convenience
    aggregated["overall"] = overall

    return aggregated

if __name__ == "__main__":
    # Initialize argument parser for command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm_model", required=False, help="The name of the LLM model used for extraction (e.g., 'gpt-4', 'gpt-3.5-turbo').")
    parser.add_argument("--version", help="The version of the extraction results to evaluate (e.g., 'version1', 'version2').")
    parser.add_argument("--material", choices=["ZnO", "IGZO", "both"], help="The material to evaluate (e.g., 'ZnO', 'IGZO', or 'both').")
    parser.add_argument("--output", default=None, help="Path to save the evaluation results as a JSON file (e.g., 'results/evaluation_summary.json').")
    
    # Parse the command-line arguments
    args = parser.parse_args()

    # Initialize LLM model
    llm_model = args.llm_model or "gpt-4o"

    # Initialize the material to evaluate
    material = args.material or "IGZO"

    # Initialize logging
    logger = LogHandler.setup_module_logging("scikg_extract", run_id=f"evaluate_{material}_{llm_model}")
    logger.info("Starting ZnO and IGZO evaluation script...")
    logger.info(f"Evaluating extraction results for LLM model: {llm_model}")
    logger.info(f"Evaluating extraction results for material: {material}")

    # Initialize the experiment version
    version = args.version or "version5"
    logger.info(f"Evaluating extraction results for version: {version}")

    # Initialize the output path
    output = args.output or os.path.join("results", "evaluation1", "ZnO-IGZO-Papers", version, "IGZO", "cross-evaluation", f"{material}_{llm_model}_evaluation_summary.json")
    logger.info(f"Evaluation results will be saved to: {output}")

    # BERTScore options
    bertscore_model = "allenai/scibert_scivocab_uncased"
    bertscore_revision = "24f92d32b1bfb0bcaf9ab193ff3ad01e87732fc1"

    # Construct the base directory path for the extraction results based on the specified version
    base_dir = os.path.join("results", "extractions1", "ZnO-IGZO-Papers", version, "experimental-usecase")
    
    # Initialize the results dictionary to store evaluation metrics for each field
    out = {}
    
    # Evaluate ZnO and IGZO extraction results based on the specified material argument and store the results in the output dictionary
    if material in ("ZnO", "both"):
        annotation_dict = {"material_deposited": [], "precursor": [], "coreactant1": [], "coreactant2": [], "coreactant3": []}
        out["ZnO"] = evaluate(base_dir, llm_model, "ZnO", compute_bertscore=True, bertscore_model=bertscore_model, bertscore_revision=bertscore_revision, results=annotation_dict)
    if material in ("IGZO", "both"):
        annotation_dict = {"material_deposited": [], "precursor1": [], "precursor2": [], "precursor3": [], "coreactant": []}
        out["IGZO"] = evaluate(base_dir, llm_model, "IGZO", compute_bertscore=True, bertscore_model=bertscore_model, bertscore_revision=bertscore_revision, results=annotation_dict)
    
    # Print the evaluation summary in the readable format
    print_evaluation_summary(out)
    
    # If an output path is specified, save the evaluation results to a JSON file
    if output:
        save_json_file(os.path.dirname(output), os.path.basename(output), out)
        logger.info(f"Evaluation results saved to: {output}")
