"""
Evaluate BioRED extraction results against gold-standard test set.
"""
# Python Imports
import os
import argparse

# SciKGExtract Evaluation Imports
from scikg_extract.evaluation.metrics import entity_precision_recall_f1, relation_precision_recall_f1, span_micro_f1, aggregate_metrics, print_evaluation_summary

# SciKGExtract Utility Imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.file_utils import read_json_file, save_json_file

if __name__ == "__main__":
    """
    Main function to evaluate BioRED extraction results against the gold-standard test set.
    """
    # Initialize the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm_model", required=False, help="The name of the LLM model used for extraction (e.g., 'gpt-4', 'gpt-3.5-turbo').")
    parser.add_argument("--experiment", help="The name of the experiment or extraction run to evaluate (e.g., 'experiment1', 'experiment2').")
    parser.add_argument("--include_keys", default="text,type", help="Comma-separated list of keys to include in entity evaluation (e.g., 'text,type').")
    parser.add_argument("--exclude_keys", default=None, help="Comma-separated list of keys to exclude from entity evaluation (e.g., 'subtype').")
    parser.add_argument("--relation_keys", default="type,entity1,entity2", help="Comma-separated list of keys to use for relation evaluation (e.g., 'type,entity1,entity2').")
    parser.add_argument("--span_f1", action="store_true", help="Whether to compute span-based Micro-F1 for entity evaluation.")
    parser.add_argument("--output", default=None, help="Path to save the evaluation results as a JSON file (e.g., 'results/evaluation_summary.json').")
    
    # Parse the command-line arguments
    args = parser.parse_args()

    # Initialize LLM model
    llm_model = args.llm_model or "gpt-4o"

    # Initialize logging
    logger = LogHandler.setup_module_logging("scikg_extract", run_id=f"evaluate_biored_{llm_model}")
    logger.info("Starting BioRED evaluation script...")
    logger.info(f"Evaluating extraction results for LLM model: {llm_model}")

    # Initialize experiment name
    experiment = args.experiment or "experiment4"
    logger.info(f"Evaluating extraction results for experiment: {experiment}")

    # Initialize the output path
    output = args.output or os.path.join("results", "evaluation1", "BioRED", experiment, "cross-evaluation", f"{llm_model}_evaluation_summary.json")
    logger.info(f"Evaluation results will be saved to: {output}")

    # Process the include and exclude keys for entity evaluation
    include_keys = [k.strip() for k in args.include_keys.split(",") if k.strip()]
    if args.exclude_keys:
        exclude = set(k.strip() for k in args.exclude_keys.split(",") if k.strip())
        include_keys = [k for k in include_keys if k not in exclude]
    
    # Process the relation keys for relation evaluation
    relation_keys = [k.strip() for k in args.relation_keys.split(",") if k.strip()]

    # BERTScore options
    bertscore_model = "allenai/scibert_scivocab_uncased"
    bertscore_revision = "24f92d32b1bfb0bcaf9ab193ff3ad01e87732fc1"

    # Construct the paths to the gold-standard test set
    gold_path = os.path.join("data", "gold-standard-datasets", "BioRED", "processed", "test.json")
    
    # Construct the path to the extraction results for the specified experiment and LLM model
    ext_dir = os.path.join("results", "extractions1", "BioRED", experiment, "test", "cross-evaluation", llm_model)
    
    # Read the gold-standard test set
    gold_docs = read_json_file(gold_path)
    
    # Initialize the results dictionary to store evaluation metrics for entities and relations
    results = {"entity": [], "relation": []}

    # If span-based Micro-F1 evaluation is requested, initialize the corresponding list in the results dictionary
    if args.span_f1:
        results["span_micro_f1"] = []

    # Iterate over each document in the gold-standard test set
    for doc in gold_docs:
        logger.info(f"Evaluating document ID: {doc['doc_id']}")
        # Extract the document ID and read the corresponding predicted extraction results
        doc_id = str(doc["doc_id"])
        ext_file = os.path.join(ext_dir, f"{doc_id}.json")
        if not os.path.exists(ext_file): continue
        pred = read_json_file(ext_file)

        # Entities Evaluation
        gold_ents = doc.get("entities", [])
        pred_ents = pred.get("entities", [])
        results["entity"].append(entity_precision_recall_f1(gold_ents, pred_ents, include_keys, compute_bertscore=True, bert_embedding_model=bertscore_model, bert_embedding_model_revision=bertscore_revision))
        
        # Relations Evaluation
        gold_rels = doc.get("relations", [])
        pred_rels = pred.get("relations", [])
        results["relation"].append(relation_precision_recall_f1(gold_rels, pred_rels, relation_keys, compute_bertscore=True, bert_embedding_model=bertscore_model, bert_embedding_model_revision=bertscore_revision))
        
        # Span-based Micro-F1
        if args.span_f1:
            results["span_micro_f1"].append(span_micro_f1(gold_ents, pred_ents))
    
    # Aggregate the evaluation metrics for entities, relations, and span-based Micro-F1 across all documents
    out = {k: aggregate_metrics(v) for k, v in results.items()}

    # Print the evaluation summary in a readable format
    print_evaluation_summary(out)

    # If an output path is specified, save the evaluation results to a JSON file
    if output:
        save_json_file(os.path.dirname(output), os.path.basename(output), out)
        logger.info(f"Evaluation results saved to: {output}")
