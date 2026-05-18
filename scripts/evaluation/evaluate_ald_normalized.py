"""
Compute precision, recall, and F1 for ALD ZnO and IGZO chemical extraction results
using PubChem CID-based normalization.

Gold chemical names are parsed from the process-condition folder path (e.g.
"ZnEt2 - H2O" → precursor="ZnEt2", co-reactant="H2O"). Predicted chemicals must
have been normalized to PubChem CIDs via sameAs URLs. A prediction is a true positive
when the gold string matches any synonym or IUPAC name stored in the CID representations
dictionary (built by scripts/pubchem/build_cid_representations.py).

Matching strategy (applied in order):
  1. Exact normalized match (NFKC + lower + whitespace collapse) against IUPAC name,
     molecular formula, or any PubChem synonym.
  2. Fuzzy similarity >= fuzz_threshold (default 85) against IUPAC name or synonyms
     using rapidfuzz token_set_ratio.

When a prediction contains multiple sameAs CIDs a match is declared if ANY of them
satisfies the above criteria. Set-based matching is used within each process so that
each gold chemical can only be counted as a TP once.
"""
# Python Imports
import argparse
import os

# SciKG-Extract Imports
from scikg_extract.evaluation.runner import run_evaluation
from scikg_extract.utils.log_handler import LogHandler

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=("Evaluate ALD ZnO/IGZO chemical extraction results using PubChem CID-based synonym matching."), formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser.add_argument("--extractions_dir", default=os.path.join("results", "extractions", "ZnO-IGZO-Papers"), metavar="DIR", help="Root directory of normalized JSON extraction results.")
    
    parser.add_argument("--experiment", default=None, metavar="NAME", help="Experiment subfolder to evaluate (e.g. experiment1, experiment4). Appended to --extractions_dir.")
    
    parser.add_argument("--judges", choices=["two_judges", "three_judges"], default=None, help="For experiment3: restrict to the two_judges or three_judges subfolder.")
    
    parser.add_argument("--evaluation_type", choices=["cross-evaluation", "self-evaluation"], default=None, help="For experiment4: restrict to cross-evaluation or self-evaluation subfolder.")
    
    parser.add_argument("--cid_representations", default=os.path.join("data", "resources", "pubchem_cid_representations.json"),
        metavar="FILE", help="CID representations JSON file (built by scripts/pubchem/build_cid_representations.py).")
    
    parser.add_argument("--llm_models", nargs="+", default=None, metavar="MODEL", help="LLM model folder name(s) to evaluate (e.g. gpt-4o llama-3.3-70b-instruct).")
    
    parser.add_argument("--material", choices=["ZnO", "IGZO"], default=None, help="Restrict evaluation to ZnO or IGZO only.")
    
    parser.add_argument("--fuzz_threshold", type=int, default=85, metavar="N", help="Minimum rapidfuzz token_set_ratio score (0-100) for fuzzy synonym matching.",)
    
    parser.add_argument("--output", default=None, metavar="FILE", help="Optional path to save JSON results.")
    
    parser.add_argument("--verbose", action="store_true", help="Print per-comparison details (gold vs predicted CIDs).")
    
    args = parser.parse_args()

    logger = LogHandler.setup_module_logging("scikg_extract", run_id="evaluate_ald_normalized")
    logger.info("Starting ALD normalized evaluation script...")

    llm_models = args.llm_models or None
    logger.info(f"Evaluating extraction results for LLM model(s): {llm_models or 'all'}")
    logger.info(f"Material filter: {args.material or 'both'}")
    logger.info(f"Experiment: {args.experiment or 'all'}")

    output = args.output

    config = {
        "extractions_dir": args.extractions_dir,
        "experiment": args.experiment,
        "cid_representations": args.cid_representations,
        "llm_models": llm_models,
        "material": args.material,
        "judges": args.judges,
        "evaluation_type": args.evaluation_type,
        "fuzz_threshold": args.fuzz_threshold,
        "verbose": args.verbose,
        "output": output,
    }

    run_evaluation("ALD_normalized", config)
