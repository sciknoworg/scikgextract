"""
Unified evaluation dispatcher for SciKGExtract.

Public interface:
    run_evaluation(dataset, config) -> dict

Supported dataset names and their config keys:

    "BC5CDR"         llm_model, experiment, gold_path, ext_dir, include_keys,
                     exclude_keys, relation_keys, compute_bertscore,
                     compute_normalized_f1, compute_soft_f1, span_f1, output

    "BioRED"         same keys as BC5CDR (different defaults)

    "PcMSP"          llm_model, experiment, gold_path, ext_dir,
                     include_categories, exclude_categories, relation_keys,
                     compute_bertscore, output

    "PolyIE"         llm_model, experiment, gold_path, ext_dir,
                     include_categories, relation_keys, compute_bertscore, output

    "ZnO" / "IGZO"   llm_model, version, material, base_dir,
                     compute_bertscore, output

    "ALD_normalized" extractions_dir, experiment, cid_representations,
                     llm_models, material, judges, evaluation_type,
                     fuzz_threshold, verbose, output
"""
# Python Imports
import os
from collections import defaultdict
from typing import Optional

# SciKGExtract Evaluation Imports
from scikg_extract.evaluation.metrics import (
    aggregate_metrics,
    entity_precision_recall_f1,
    print_evaluation_summary,
    relation_precision_recall_f1,
    save_evaluation_results,
    span_micro_f1,
)
from scikg_extract.evaluation.pubchem_normalized_matching import (
    _compute_metrics,
    _compute_metrics_any_match,
    _field_cids,
    _field_value,
    _parse_folder_annotations,
    _pred_matches_gold,
)

# SciKGExtract Utility Imports
from scikg_extract.utils.file_utils import read_json_file
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.string_utils import normalize_entity_list, normalize_relation_list

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_BERTSCORE_MODEL = "allenai/scibert_scivocab_uncased"
_BERTSCORE_REVISION = "24f92d32b1bfb0bcaf9ab193ff3ad01e87732fc1"

# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def run_evaluation(dataset: str, config: dict) -> dict:
    """
    Run evaluation for a named dataset and return the aggregated metrics dict.

    Args:
        dataset: One of "BC5CDR", "BioRED", "PcMSP", "PolyIE", "ZnO", "IGZO", "ALD_normalized".
        config:  Dataset-specific configuration dict. All keys are optional.
    Returns:
        Aggregated evaluation results dict.
    Raises:
        ValueError: If dataset is not recognised.
        jsonschema.ValidationError: If the results don't conform to the evaluation schema (raised by save_evaluation_results).
    """
    _dispatch = {
        "BC5CDR": _run_bc5cdr,
        "BioRED": _run_biored,
        "PcMSP": _run_pcmsp,
        "PolyIE": _run_polyie,
        "ZnO": _run_zno_igzo,
        "IGZO": _run_zno_igzo,
        "ALD_normalized": _run_ald_normalized,
    }
    if dataset not in _dispatch:
        raise ValueError(f"Unknown dataset {dataset!r}. Must be one of: {sorted(_dispatch)}")

    results = _dispatch[dataset](dataset, config)

    output = config.get("output")
    if output:
        out_dir = os.path.dirname(os.path.abspath(output))
        os.makedirs(out_dir, exist_ok=True)
        save_evaluation_results(results, output)
        LogHandler.get_logger("scikg_extract").info("Results saved to: %s", output)

    print_evaluation_summary(results)
    return results


# ---------------------------------------------------------------------------
# BC5CDR evaluator
# ---------------------------------------------------------------------------

def _run_bc5cdr(dataset: str, config: dict) -> dict:
    """
    Evaluate BC5CDR: flat doc list, entity/relation matching by doc_id.

    Config defaults:
        llm_model              "claude-sonnet-4.6"
        experiment             "experiment1"
        gold_path              data/gold-standard-datasets/BC5CDR/processed/test.json
        ext_dir                results/extractions/BC5CDR/{experiment}/test/{llm_model}
        include_keys           ["text", "type"]
        exclude_keys           None
        relation_keys          ["type", "chemical", "disease"]
        compute_bertscore      False
        compute_normalized_f1  True
        compute_soft_f1        True
        span_f1                False
    """
    logger = LogHandler.get_logger("scikg_extract")
    llm_model = config.get("llm_model", "claude-sonnet-4.6")
    experiment = config.get("experiment", "experiment1")
    gold_path = config.get(
        "gold_path",
        os.path.join("data", "gold-standard-datasets", "BC5CDR", "processed", "test.json"),
    )
    ext_dir = config.get(
        "ext_dir",
        os.path.join("results", "extractions", "BC5CDR", experiment, "test", llm_model),
    )
    include_keys = config.get("include_keys", ["text", "type"])
    if config.get("exclude_keys"):
        exclude = set(config["exclude_keys"])
        include_keys = [k for k in include_keys if k not in exclude]
    relation_keys = config.get("relation_keys", ["type", "chemical", "disease"])
    compute_bertscore = config.get("compute_bertscore", False)
    compute_normalized_f1 = config.get("compute_normalized_f1", True)
    compute_soft_f1 = config.get("compute_soft_f1", True)
    use_span_f1 = config.get("span_f1", False)

    gold_docs = read_json_file(gold_path)
    results: dict = {"entity": [], "relation": []}
    if use_span_f1:
        results["span_micro_f1"] = []

    for doc in gold_docs:
        logger.info("Evaluating BC5CDR document ID: %s", doc.get("doc_id"))
        doc_id = str(doc["doc_id"])
        ext_file = os.path.join(ext_dir, f"{doc_id}.json")
        if not os.path.exists(ext_file):
            continue
        pred = read_json_file(ext_file)

        gold_ents = doc.get("entities", [])
        pred_ents = pred.get("entities", [])
        results["entity"].append(
            entity_precision_recall_f1(
                gold_ents, pred_ents, include_keys,
                compute_bertscore=compute_bertscore,
                bert_embedding_model=_BERTSCORE_MODEL,
                bert_embedding_model_revision=_BERTSCORE_REVISION,
                compute_normalized_f1=compute_normalized_f1,
                compute_soft_f1=compute_soft_f1,
            )
        )

        gold_rels = doc.get("relations", [])
        pred_rels = pred.get("relations", [])
        results["relation"].append(
            relation_precision_recall_f1(
                gold_rels, pred_rels, relation_keys,
                compute_bertscore=compute_bertscore,
                bert_embedding_model=_BERTSCORE_MODEL,
                bert_embedding_model_revision=_BERTSCORE_REVISION,
                compute_normalized_f1=compute_normalized_f1,
                compute_soft_f1=compute_soft_f1,
            )
        )

        if use_span_f1:
            results["span_micro_f1"].append(span_micro_f1(gold_ents, pred_ents))

    return {k: aggregate_metrics(v) for k, v in results.items()}


# ---------------------------------------------------------------------------
# BioRED evaluator
# ---------------------------------------------------------------------------

def _run_biored(dataset: str, config: dict) -> dict:
    """
    Evaluate BioRED: flat doc list, entity/relation matching by doc_id.

    Config defaults:
        llm_model              "gpt-4o"
        experiment             "experiment4"
        gold_path              data/gold-standard-datasets/BioRED/processed/test.json
        ext_dir                results/extractions1/BioRED/{experiment}/test/{llm_model}
        include_keys           ["text", "type"]
        exclude_keys           None
        relation_keys          ["type", "entity1", "entity2"]
        compute_bertscore      True
        compute_normalized_f1  False
        compute_soft_f1        False
        span_f1                False
    """
    logger = LogHandler.get_logger("scikg_extract")
    llm_model = config.get("llm_model", "gpt-4o")
    experiment = config.get("experiment", "experiment4")
    gold_path = config.get(
        "gold_path",
        os.path.join("data", "gold-standard-datasets", "BioRED", "processed", "test.json"),
    )
    ext_dir = config.get(
        "ext_dir",
        os.path.join(
            "results", "extractions", "BioRED", experiment, "test", llm_model,
        ),
    )
    include_keys = config.get("include_keys", ["text", "type"])
    if config.get("exclude_keys"):
        exclude = set(config["exclude_keys"])
        include_keys = [k for k in include_keys if k not in exclude]
    relation_keys = config.get("relation_keys", ["type", "entity1", "entity2"])
    compute_bertscore = config.get("compute_bertscore", True)
    compute_normalized_f1 = config.get("compute_normalized_f1", False)
    compute_soft_f1 = config.get("compute_soft_f1", False)
    use_span_f1 = config.get("span_f1", False)

    gold_docs = read_json_file(gold_path)
    results: dict = {"entity": [], "relation": []}
    if use_span_f1:
        results["span_micro_f1"] = []

    for doc in gold_docs:
        logger.info("Evaluating BioRED document ID: %s", doc.get("doc_id"))
        doc_id = str(doc["doc_id"])
        ext_file = os.path.join(ext_dir, f"{doc_id}.json")
        if not os.path.exists(ext_file):
            continue
        pred = read_json_file(ext_file)

        gold_ents = doc.get("entities", [])
        pred_ents = pred.get("entities", [])
        results["entity"].append(
            entity_precision_recall_f1(
                gold_ents, pred_ents, include_keys,
                compute_bertscore=compute_bertscore,
                bert_embedding_model=_BERTSCORE_MODEL,
                bert_embedding_model_revision=_BERTSCORE_REVISION,
                compute_normalized_f1=compute_normalized_f1,
                compute_soft_f1=compute_soft_f1,
            )
        )

        gold_rels = doc.get("relations", [])
        pred_rels = pred.get("relations", [])
        results["relation"].append(
            relation_precision_recall_f1(
                gold_rels, pred_rels, relation_keys,
                compute_bertscore=compute_bertscore,
                bert_embedding_model=_BERTSCORE_MODEL,
                bert_embedding_model_revision=_BERTSCORE_REVISION,
                compute_normalized_f1=compute_normalized_f1,
                compute_soft_f1=compute_soft_f1,
            )
        )

        if use_span_f1:
            results["span_micro_f1"].append(span_micro_f1(gold_ents, pred_ents))

    return {k: aggregate_metrics(v) for k, v in results.items()}


# ---------------------------------------------------------------------------
# PcMSP evaluator
# ---------------------------------------------------------------------------

def _run_pcmsp(dataset: str, config: dict) -> dict:
    """
    Evaluate PcMSP: category-based entity evaluation, index-based file lookup.

    Config defaults:
        llm_model           "gpt-4o"
        experiment          "experiment4"
        gold_path           data/gold-standard-datasets/PcMSP/processed/test.json
        ext_dir             results/extractions1/PcMSP/{experiment}/test/{llm_model}
        include_categories  ["materials","operations","descriptors","values",
                             "properties","devices","brands"]
        exclude_categories  None
        relation_keys       ["type", "source", "target"]
        compute_bertscore   True
    """
    logger = LogHandler.get_logger("scikg_extract")
    llm_model = config.get("llm_model", "gpt-4o")
    experiment = config.get("experiment", "experiment4")
    gold_path = config.get(
        "gold_path",
        os.path.join("data", "gold-standard-datasets", "PcMSP", "processed", "test.json"),
    )
    ext_dir = config.get(
        "ext_dir",
        os.path.join(
            "results", "extractions", "PcMSP", experiment, "test", llm_model,
        ),
    )
    include_cats = list(
        config.get(
            "include_categories",
            ["materials", "operations", "descriptors", "values", "properties", "devices", "brands"],
        )
    )
    if config.get("exclude_categories"):
        exclude = set(config["exclude_categories"])
        include_cats = [c for c in include_cats if c not in exclude]
    relation_keys = config.get("relation_keys", ["type", "source", "target"])
    compute_bertscore = config.get("compute_bertscore", True)

    gold_docs = read_json_file(gold_path)
    results: dict = {cat: [] for cat in include_cats}
    results["relation"] = []

    for idx, doc in enumerate(gold_docs):
        logger.info("Evaluating PcMSP document %d/%d …", idx + 1, len(gold_docs))
        ext_file = os.path.join(ext_dir, f"{idx}.json")
        if not os.path.exists(ext_file):
            continue
        pred = read_json_file(ext_file)

        gold_ents = doc.get("entities", {})
        pred_ents = pred.get("entities", {})

        for cat in include_cats:
            gold_list = normalize_entity_list(gold_ents.get(cat, []))
            pred_list = normalize_entity_list(pred_ents.get(cat, []))
            keys = (
                ["text", "subtype"]
                if any(
                    isinstance(e, dict) and "subtype" in e
                    for e in gold_list + pred_list
                )
                else ["text"]
            )
            results[cat].append(
                entity_precision_recall_f1(
                    gold_list, pred_list, keys,
                    compute_bertscore=compute_bertscore,
                    bert_embedding_model=_BERTSCORE_MODEL,
                    bert_embedding_model_revision=_BERTSCORE_REVISION,
                )
            )

        gold_rels = normalize_relation_list(doc.get("relations", []))
        pred_rels = normalize_relation_list(pred.get("relations", []))
        results["relation"].append(
            relation_precision_recall_f1(
                gold_rels, pred_rels, relation_keys,
                compute_bertscore=compute_bertscore,
                bert_embedding_model=_BERTSCORE_MODEL,
                bert_embedding_model_revision=_BERTSCORE_REVISION,
            )
        )

    return {k: aggregate_metrics(v) for k, v in results.items()}


# ---------------------------------------------------------------------------
# PolyIE evaluator
# ---------------------------------------------------------------------------

def _run_polyie(dataset: str, config: dict) -> dict:
    """
    Evaluate PolyIE: sentence-level entity/relation evaluation, index-based
    file lookup.

    Config defaults:
        llm_model           "llama-3.3-70b-instruct"
        experiment          "experiment4"
        gold_path           data/gold-standard-datasets/PolyIE/processed/test.json
        ext_dir             results/extractions1/PolyIE/{experiment}/test/{llm_model}
        include_categories  ["chemicalNames","propertyNames","propertyValues","conditions"]
        relation_keys       ["chemicalName","propertyName","propertyValue"]
        compute_bertscore   True
    """
    logger = LogHandler.get_logger("scikg_extract")
    llm_model = config.get("llm_model", "llama-3.3-70b-instruct")
    experiment = config.get("experiment", "experiment4")
    gold_path = config.get(
        "gold_path",
        os.path.join("data", "gold-standard-datasets", "PolyIE", "processed", "test.json"),
    )
    ext_dir = config.get(
        "ext_dir",
        os.path.join(
            "results", "extractions", "PolyIE", experiment, "test", llm_model,
        ),
    )
    include_cats = list(
        config.get(
            "include_categories",
            ["chemicalNames", "propertyNames", "propertyValues", "conditions"],
        )
    )
    relation_keys = config.get(
        "relation_keys", ["chemicalName", "propertyName", "propertyValue"]
    )
    compute_bertscore = config.get("compute_bertscore", True)

    gold_docs = read_json_file(gold_path)
    results: dict = {cat: [] for cat in include_cats}
    results["relation"] = []

    for idx, doc in enumerate(gold_docs):
        logger.info("Evaluating PolyIE document %d/%d …", idx + 1, len(gold_docs))
        ext_file = os.path.join(ext_dir, f"{idx}.json")
        if not os.path.exists(ext_file):
            continue
        pred = read_json_file(ext_file)

        gold_sents = doc.get("sentences", [])
        pred_sents = pred.get("sentences", [])

        for sidx, gold_sent in enumerate(gold_sents):
            if sidx >= len(pred_sents):
                continue
            pred_sent = pred_sents[sidx]
            gold_ents = gold_sent.get("entities", {})
            pred_ents = pred_sent.get("entities", {})

            for cat in include_cats:
                gold_list = normalize_entity_list(gold_ents.get(cat, []))
                pred_list = normalize_entity_list(pred_ents.get(cat, []))
                results[cat].append(
                    entity_precision_recall_f1(
                        gold_list, pred_list, ["text"],
                        compute_bertscore=compute_bertscore,
                        bert_embedding_model=_BERTSCORE_MODEL,
                        bert_embedding_model_revision=_BERTSCORE_REVISION,
                    )
                )

            gold_rels = normalize_relation_list(gold_sent.get("relations", []))
            pred_rels = normalize_relation_list(pred_sent.get("relations", []))
            results["relation"].append(
                relation_precision_recall_f1(
                    gold_rels, pred_rels, relation_keys,
                    compute_bertscore=compute_bertscore,
                    bert_embedding_model=_BERTSCORE_MODEL,
                    bert_embedding_model_revision=_BERTSCORE_REVISION,
                )
            )

    return {k: aggregate_metrics(v) for k, v in results.items()}


# ---------------------------------------------------------------------------
# ZnO / IGZO evaluator (AtomicLimits folder-annotation pattern)
# ---------------------------------------------------------------------------

def parse_atomiclimits_annotation(folder_name: str, material: str) -> dict:
    """
    Parse an AtomicLimits process-condition folder name into a structured
    gold-standard annotation dict.

    Args:
        folder_name: Folder name encoding process conditions
                     (e.g. "ZnMe2 - O2 plasma").
        material:    "ZnO" or "IGZO".

    Returns:
        Dict with fields material_deposited, precursor / coreactant1 … (ZnO)
        or precursor1/2/3 / coreactant (IGZO).
    """
    segments = folder_name.split(" - ")
    if material == "IGZO":
        return {
            "material_deposited": material,
            "precursor1": segments[0] if len(segments) > 0 else "",
            "precursor2": segments[1] if len(segments) > 1 else "",
            "precursor3": segments[2] if len(segments) > 2 else "",
            "coreactant":  segments[3] if len(segments) > 3 else "",
        }
    return {
        "material_deposited": material,
        "precursor":   segments[0] if len(segments) > 0 else "",
        "coreactant1": segments[1] if len(segments) > 1 else "",
        "coreactant2": segments[2] if len(segments) > 2 else "",
        "coreactant3": segments[3] if len(segments) > 3 else "",
    }


def evaluate_zno_igzo(base_dir: str, llm_model: str, material: str, compute_bertscore: bool = False, bertscore_model: Optional[str] = None, bertscore_revision: Optional[str] = None, results: Optional[dict] = None) -> dict:
    """
    Evaluate ZnO or IGZO extraction results against AtomicLimits gold-standard annotations derived from process-condition folder names.

    Args:
        base_dir:          Base directory containing material subdirectories with extraction results.
        llm_model:         LLM model folder name used during extraction.
        material:          "ZnO" or "IGZO".
        compute_bertscore: Whether to compute BERTScore for field values.
        bertscore_model:   HuggingFace model name for BERTScore.
        bertscore_revision: Commit hash for reproducible BERTScore.
        results:           Optional pre-initialised accumulator dict. If omitted, an appropriate empty dict is created for the material.
    Returns:
        Aggregated metrics dict with per-field entries plus an "overall" key.
    """
    logger = LogHandler.get_logger("scikg_extract")

    if not results:
        if material == "IGZO":
            results = {
                "material_deposited": [],
                "precursor1": [],
                "precursor2": [],
                "precursor3": [],
                "coreactant": [],
            }
        else:
            results = {
                "material_deposited": [],
                "precursor": [],
                "coreactant1": [],
                "coreactant2": [],
                "coreactant3": [],
            }

    mat_dir = os.path.join(base_dir, material)
    atomic_db_dir = (
        os.path.join(mat_dir, "AtomicLimits Database")
        if material == "IGZO"
        else mat_dir
    )

    for proc_cond in os.listdir(atomic_db_dir):
        proc_path = os.path.join(atomic_db_dir, proc_cond, llm_model)
        if not os.path.isdir(proc_path):
            continue

        for fname in os.listdir(proc_path):
            if not fname.endswith(".json"):
                continue
            logger.info("Evaluating process condition: %s  file: %s", proc_cond, fname)
            pred = read_json_file(os.path.join(proc_path, fname))
            annotation = parse_atomiclimits_annotation(proc_cond, material)

            for field in results:
                gold = [{"value": annotation[field]}]
                if not gold[0]["value"]:
                    continue

                for entry in pred.get("processes", []):
                    if field == "material_deposited":
                        pred_val = entry.get("aldSystem", {}).get("materialDeposited", "")
                        logger.debug(
                            "material_deposited | gold=%r pred=%r", gold, pred_val
                        )
                        results[field].append(
                            entity_precision_recall_f1(
                                gold,
                                [{"value": pred_val}] if pred_val else [],
                                ["value"],
                                compute_bertscore=compute_bertscore,
                                bert_embedding_model=bertscore_model,
                                bert_embedding_model_revision=bertscore_revision,
                            )
                        )
                    elif field.startswith("precursor"):
                        pred_val_list = entry.get("reactantSelection", {}).get("precursor", [])
                        for pred_val in pred_val_list:
                            pred_list = (
                                [{"value": pred_val.get("precursor", "")}]
                                if pred_val else []
                            )
                            logger.debug(
                                "%s | gold=%r pred=%r", field, gold, pred_list
                            )
                            results[field].append(
                                entity_precision_recall_f1(
                                    gold, pred_list, ["value"],
                                    compute_bertscore=compute_bertscore,
                                    bert_embedding_model=bertscore_model,
                                    bert_embedding_model_revision=bertscore_revision,
                                )
                            )
                    elif field.startswith("coreactant"):
                        pred_val_list = entry.get("reactantSelection", {}).get("coReactant", [])
                        for pred_val in pred_val_list:
                            pred_list = (
                                [{"value": pred_val.get("coReactant", "")}]
                                if pred_val else []
                            )
                            logger.debug(
                                "%s | gold=%r pred=%r", field, gold, pred_list
                            )
                            results[field].append(
                                entity_precision_recall_f1(
                                    gold, pred_list, ["value"],
                                    compute_bertscore=compute_bertscore,
                                    bert_embedding_model=bertscore_model,
                                    bert_embedding_model_revision=bertscore_revision,
                                )
                            )

    aggregated = {k: aggregate_metrics(v) for k, v in results.items()}

    total_tp = sum(m.get("tp", 0) for m in aggregated.values())
    total_fp = sum(m.get("fp", 0) for m in aggregated.values())
    total_fn = sum(m.get("fn", 0) for m in aggregated.values())
    overall_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    overall_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    overall_f = (
        2 * overall_p * overall_r / (overall_p + overall_r)
        if (overall_p + overall_r) > 0 else 0.0
    )
    overall: dict = {
        "precision": overall_p,
        "recall":    overall_r,
        "f1":        overall_f,
        "tp":        total_tp,
        "fp":        total_fp,
        "fn":        total_fn,
    }
    bs_list = [
        m.get("bertscore")
        for m in aggregated.values()
        if isinstance(m.get("bertscore"), dict)
    ]
    if bs_list:
        overall["bertscore"] = {
            "precision": sum(float(b.get("precision", 0.0)) for b in bs_list) / len(bs_list),
            "recall":    sum(float(b.get("recall", 0.0)) for b in bs_list) / len(bs_list),
            "f1":        sum(float(b.get("f1", 0.0)) for b in bs_list) / len(bs_list),
        }
    aggregated["overall"] = overall
    return aggregated


def _run_zno_igzo(dataset: str, config: dict) -> dict:
    """
    Evaluate ZnO and/or IGZO (AtomicLimits pattern).

    When called via run_evaluation("ZnO", ...) or run_evaluation("IGZO", ...) the ``dataset`` argument determines the material.  Pass ``material="both"`` in config to evaluate both materials; the result is then nested: {"ZnO": {...}, "IGZO": {...}}.

    Config defaults:
        llm_model         "gpt-4o"
        version           "version5"
        material          dataset name (i.e. "ZnO" or "IGZO"), or "both"
        base_dir          results/extractions1/ZnO-IGZO-Papers/{version}/experimental-usecase
        compute_bertscore True
    """
    llm_model = config.get("llm_model", "gpt-4o")
    version = config.get("version", "version5")
    material = config.get("material", dataset)  # default to the dataset key
    compute_bertscore = config.get("compute_bertscore", True)
    bertscore_model = _BERTSCORE_MODEL
    bertscore_revision = _BERTSCORE_REVISION
    base_dir = config.get(
        "base_dir",
        os.path.join(
            "results", "extractions", "ZnO-IGZO-Papers", version, "experimental-usecase"
        ),
    )

    out: dict = {}
    if material in ("ZnO", "both"):
        annotation_dict: dict = {
            "material_deposited": [], "precursor": [],
            "coreactant1": [], "coreactant2": [], "coreactant3": [],
        }
        out["ZnO"] = evaluate_zno_igzo(
            base_dir, llm_model, "ZnO",
            compute_bertscore=compute_bertscore,
            bertscore_model=bertscore_model,
            bertscore_revision=bertscore_revision,
            results=annotation_dict,
        )
    if material in ("IGZO", "both"):
        annotation_dict = {
            "material_deposited": [], "precursor1": [], "precursor2": [],
            "precursor3": [], "coreactant": [],
        }
        out["IGZO"] = evaluate_zno_igzo(
            base_dir, llm_model, "IGZO",
            compute_bertscore=compute_bertscore,
            bertscore_model=bertscore_model,
            bertscore_revision=bertscore_revision,
            results=annotation_dict,
        )

    return out


# ---------------------------------------------------------------------------
# ALD normalized evaluator (PubChem CID-based matching)
# ---------------------------------------------------------------------------

def evaluate_ald_normalized(extractions_dir: str, cid_repr: dict, llm_models: Optional[list] = None, material_filter: Optional[str] = None, judges_filter: Optional[str] = None, evaluation_type_filter: Optional[str] = None, fuzz_threshold: int = 85, verbose: bool = False) -> dict:
    """
    Walk extractions_dir and compute CID-based P/R/F1 for ALD chemical extraction (ZnO / IGZO normalised results).

    Returns:
        Dict with category keys (material_deposited, precursor, co_reactant, overall) → aggregated metrics.
    """
    logger = LogHandler.get_logger("evaluate_ald_normalized")
    category_metrics: dict = defaultdict(list)
    file_count = 0

    for root, _, files in os.walk(extractions_dir):
        json_files = [f for f in files if f.endswith(".json")]
        if not json_files:
            continue

        llm_in_path = os.path.normpath(root).split(os.sep)[-1]
        if llm_models and llm_in_path not in llm_models:
            continue

        material, annotations, judges, evaluation_type = _parse_folder_annotations(root)
        if not material:
            continue
        if material_filter and material != material_filter:
            continue
        if judges_filter and judges != judges_filter:
            continue
        if evaluation_type_filter and evaluation_type != evaluation_type_filter:
            continue
        if not annotations:
            continue

        for fname in json_files:
            fp = os.path.join(root, fname)
            data = read_json_file(fp)
            if not data:
                logger.warning("No data in %s, skipping.", fp)
                continue
            file_count += 1

            for proc in data.get("processes", []):
                ald_system = proc.get("aldSystem", {})
                reactant_sel = proc.get("reactantSelection", {})

                mat_field = ald_system.get("materialDeposited")
                pred_mat_cid_lists = [_field_cids(mat_field)] if mat_field is not None else [[]]
                pred_mat_raw = [_field_value(mat_field)] if mat_field is not None else [None]
                mat_m = _compute_metrics(
                    [material], pred_mat_cid_lists, cid_repr,
                    fuzz_threshold, pred_raw_values=pred_mat_raw,
                )
                category_metrics["material_deposited"].append(mat_m)

                if verbose:
                    status = "TP" if mat_m["tp"] else ("FP" if mat_m["fp"] else "FN")
                    print(
                        f"  [{status}] material_deposited | gold={material!r} | "
                        f"value={pred_mat_raw[0]!r} | "
                        f"pred_cids={pred_mat_cid_lists[0] if pred_mat_cid_lists else []}"
                    )

                if material == "IGZO":
                    gold_prec = annotations[:-1]
                    co_gold = [annotations[-1]] if annotations else []
                else:
                    gold_prec = [annotations[0]] if annotations else []
                    co_gold = annotations[1:]

                if len(annotations) > 1:
                    pred_precs = reactant_sel.get("precursor", [])
                    pred_prec_cid_lists = [
                        _field_cids(p.get("precursor")) for p in pred_precs
                    ]
                    pred_prec_raw = [
                        _field_value(p.get("precursor")) for p in pred_precs
                    ]
                    prec_m = _compute_metrics_any_match(
                        gold_prec, pred_prec_cid_lists, cid_repr,
                        fuzz_threshold, pred_raw_values=pred_prec_raw,
                    )
                    category_metrics["precursor"].append(prec_m)

                    if verbose:
                        for gold_s in gold_prec:
                            matched = any(
                                _pred_matches_gold(cids, rv, gold_s, cid_repr, fuzz_threshold)
                                for cids, rv in zip(pred_prec_cid_lists, pred_prec_raw)
                            )
                            print(
                                f"  [{'TP' if matched else 'FN'}] precursor | "
                                f"gold={gold_s!r} | pred_count={len(pred_prec_cid_lists)}"
                            )

                pred_coreacs = reactant_sel.get("coReactant", [])
                pred_coreac_cid_lists = [
                    _field_cids(c.get("coReactant")) for c in pred_coreacs
                ]
                pred_coreac_raw = [
                    _field_value(c.get("coReactant")) for c in pred_coreacs
                ]
                if co_gold or pred_coreac_cid_lists:
                    coreac_m = _compute_metrics(
                        co_gold, pred_coreac_cid_lists, cid_repr,
                        fuzz_threshold, pred_raw_values=pred_coreac_raw,
                    )
                    category_metrics["co_reactant"].append(coreac_m)

    logger.info("Processed %d extraction files.", file_count)

    results: dict = {
        cat: aggregate_metrics(metrics_list)
        for cat, metrics_list in category_metrics.items()
    }
    all_metrics = [m for ml in category_metrics.values() for m in ml]
    if all_metrics:
        results["overall"] = aggregate_metrics(all_metrics)

    return results


def _run_ald_normalized(dataset: str, config: dict) -> dict:
    """
    Evaluate ALD normalised chemical extractions using PubChem CID matching.

    Config defaults:
        extractions_dir    "results/extractions/ZnO-IGZO-Papers"
        experiment         None  (no subfolder appended)
        cid_representations "data/resources/pubchem_cid_representations.json"
        llm_models         None  (all models)
        material           None  (both ZnO and IGZO)
        judges             None  (all judge variants)
        evaluation_type    None  (all evaluation types)
        fuzz_threshold     85
        verbose            False
    """
    logger = LogHandler.get_logger("scikg_extract")
    extractions_dir = config.get(
        "extractions_dir",
        os.path.join("results", "extractions", "ZnO-IGZO-Papers"),
    )
    experiment = config.get("experiment")
    if experiment:
        extractions_dir = os.path.join(extractions_dir, experiment)

    cid_repr_path = config.get(
        "cid_representations",
        os.path.join("data", "resources", "pubchem_cid_representations.json"),
    )
    cid_repr = read_json_file(cid_repr_path)
    if not cid_repr:
        logger.error(
            "Could not load CID representations from %s. "
            "Run scripts/pubchem/build_cid_representations.py first.",
            cid_repr_path,
        )
        return {}

    return evaluate_ald_normalized(
        extractions_dir=extractions_dir,
        cid_repr=cid_repr,
        llm_models=config.get("llm_models"),
        material_filter=config.get("material"),
        judges_filter=config.get("judges"),
        evaluation_type_filter=config.get("evaluation_type"),
        fuzz_threshold=config.get("fuzz_threshold", 85),
        verbose=config.get("verbose", False),
    )
