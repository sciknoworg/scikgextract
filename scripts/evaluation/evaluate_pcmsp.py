"""
Evaluate PcMSP extraction results against gold-standard test set.
"""
# Python Imports
import os
import codecs
import argparse

# SciKGExtract Evaluation Imports
from scikg_extract.evaluation.metrics import entity_precision_recall_f1, relation_precision_recall_f1, aggregate_metrics, print_evaluation_summary

# SciKGExtract Utility Imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import read_json_file, save_json_file

def _decode_unicode_escapes(s) -> str:
    """
    Decode unicode-escaped sequences in a string (e.g., "\\u00b0" -> "°").
    Args:
        s (str): The input string that may contain unicode-escaped sequences
    Returns:
        str: The decoded string with unicode-escaped sequences converted to their actual characters
    """
    if not isinstance(s, str): return s
    
    # Only attempt decode if we see a backslash-u pattern
    if "\\u" in s:
        try:
            return s.encode("utf-8").decode("unicode_escape")
        except Exception:
            try:
                return codecs.decode(s, "unicode_escape")
            except Exception:
                return s
    return s

def _normalize_entity_list(ent_list) -> list:
    """
    Normalize entity lists by converting string entries to dicts with 'text' key and decoding escaped unicode sequences.
    Args:
        ent_list (list): The list of entities to be normalized, which may contain dicts or strings
    Returns:
        list: The normalized list of entities, where all entries are dicts and any escaped unicode sequences in string fields are decoded
    """
    # If the entity list is not actually a list, return an empty list to avoid errors in metrics functions
    if not isinstance(ent_list, list): return []
    
    # Normalize entries so metrics functions receive dicts and decode escaped unicode in string fields
    normalized = []
    for e in ent_list:
        if isinstance(e, dict):
            new_e = {}
            for k, v in e.items():
                new_e[k] = _decode_unicode_escapes(v) if isinstance(v, str) else v
            normalized.append(new_e)
        elif isinstance(e, str):
            normalized.append({"text": _decode_unicode_escapes(e)})
        else:
            normalized.append({"text": str(e)})
    return normalized

def _normalize_relation_list(rel_list) -> list:
    """
    Normalize relation lists by decoding escaped unicode sequences in string fields.
    Args:
        rel_list (list): The list of relations to be normalized, which may contain dicts or strings
    Returns:
        list: The normalized list of relations, where any escaped unicode sequences in string fields are decoded.
    """
    # If the relation list is not actually a list, return an empty list to avoid errors in metrics functions
    if not isinstance(rel_list, list): return []

    # Normalize entries to decode escaped unicode in string fields
    normalized = []
    for r in rel_list:
        if isinstance(r, dict):
            new_r = {}
            for k, v in r.items():
                new_r[k] = _decode_unicode_escapes(v) if isinstance(v, str) else v
            normalized.append(new_r)
        else:
            normalized.append(r)
    return normalized

if __name__ == "__main__":
    """
    Main function to evaluate PcMSP extraction results against the gold-standard test set.
    """
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
    output = args.output or os.path.join("results", "evaluation1", "PcMSP", experiment, "cross-evaluation", f"{llm_model}_evaluation_summary.json")
    logger.info(f"Evaluation results will be saved to: {output}")

    # Process the include and exclude categories for entity evaluation
    include_cats = [c.strip() for c in args.include_categories.split(",") if c.strip()]
    if args.exclude_categories:
        exclude = set(c.strip() for c in args.exclude_categories.split(",") if c.strip())
        include_cats = [c for c in include_cats if c not in exclude]
    
    # Process the relation keys for relation evaluation
    relation_keys = [k.strip() for k in args.relation_keys.split(",") if k.strip()]

    # BERTScore options
    bertscore_model = "allenai/scibert_scivocab_uncased"
    bertscore_revision = "24f92d32b1bfb0bcaf9ab193ff3ad01e87732fc1"

    # Construct the paths to the gold-standard test set
    gold_path = os.path.join("data", "gold-standard-datasets", "PcMSP", "processed", "test.json")

    # Construct the path to the extraction results for the specified experiment and LLM model
    ext_dir = os.path.join("results", "extractions1", "PcMSP", experiment, "test", "cross-evaluation", llm_model)

    # Read the gold-standard test set
    gold_docs = read_json_file(gold_path)
    
    # Initialize the results dictionary to store evaluation metrics for each entity category and relations
    results = {cat: [] for cat in include_cats}
    results["relation"] = []

    # Iterate over each document in the gold-standard test set
    for idx, doc in enumerate(gold_docs):
        logger.info(f"Evaluating document {idx+1}/{len(gold_docs)}...")
        # Read the corresponding predicted extraction results for the current document
        ext_file = os.path.join(ext_dir, f"{idx}.json")
        if not os.path.exists(ext_file): continue
        pred = read_json_file(ext_file)

        # Extract the gold-standard annotations for the current document
        gold_ents = doc.get("entities", {})

        # Extract the predicted entities for the current document
        pred_ents = pred.get("entities", {})

        # Evaluate each specified entity category
        for cat in include_cats:

            # Extract the gold and predicted entity lists for the current category
            gold_list = gold_ents.get(cat, [])
            pred_list = pred_ents.get(cat, [])

            # Normalize entries so metrics functions receive dicts (they expect dicts with .get)
            gold_list = _normalize_entity_list(gold_list)
            pred_list = _normalize_entity_list(pred_list)

            # For materials/properties, match on text+subtype if present, else just text
            keys = ["text", "subtype"] if any(isinstance(e, dict) and "subtype" in e for e in gold_list + pred_list) else ["text"]

            # Compute precision, recall, and F1 for the current category and append the metrics to the results
            results[cat].append(entity_precision_recall_f1(gold_list, pred_list, keys, compute_bertscore=True, bert_embedding_model=bertscore_model, bert_embedding_model_revision=bertscore_revision))

        # Relations Evaluation
        gold_rels = _normalize_relation_list(doc.get("relations", []))
        pred_rels = _normalize_relation_list(pred.get("relations", []))
        results["relation"].append(relation_precision_recall_f1(gold_rels, pred_rels, relation_keys, compute_bertscore=True, bert_embedding_model=bertscore_model, bert_embedding_model_revision=bertscore_revision))
    
    # Aggregate the evaluation metrics for each entity category and relations across all documents
    out = {k: aggregate_metrics(v) for k, v in results.items()}

    # Print the evaluation summary in a readable format
    print_evaluation_summary(out)

    # If an output path is specified, save the evaluation results to a JSON file
    if output: 
        save_json_file(os.path.dirname(output), os.path.basename(output), out)
        logger.info(f"Evaluation results saved to: {output}")
