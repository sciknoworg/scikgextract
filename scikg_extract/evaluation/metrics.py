"""
Metric computation functions for entity/relation extraction evaluation. Includes precision, recall, F1 for entities and relations based on configurable matching keys, as well as span-based micro-F1 for NER tasks. Also includes utilities for aggregating metrics across documents and saving/printing results.
"""
# Python Imports
import json
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Third-party Imports
import jsonschema

# SciKGExtract Utils Imports
from scikg_extract.utils.log_handler import LogHandler

# SKLearn Imports
import numpy as _np
from scipy.optimize import linear_sum_assignment as _linear_sum_assignment
import evaluate as _evaluate
from typing import Iterable

def _to_tuple(d: Dict[str, Any], keys: List[str]) -> Tuple:
    """
    Convert dict to tuple of selected keys for set comparison. Missing keys will be None.
    Example:
    d = {"text": "Aspirin", "type": "Chemical", "offset": 10}
    keys = ["text", "type"] -> ("Aspirin", "Chemical")
    Args:
        d: Input dictionary representing an entity or relation.
        keys: List of keys to extract from the dictionary for matching.
    Returns:
        Tuple: A tuple of values corresponding to the specified keys, used for set-based metric computation.
    """
    return tuple(d.get(k, None) for k in keys)

def _normalize(s: str) -> str:
    """
    Normalize a string for lenient matching: NFKC unicode normalization, lowercase,
    strip leading/trailing whitespace, collapse internal whitespace.
    Follows the normalization approach used in SQuAD evaluation (Rajpurkar et al., 2016).
    """
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    s = " ".join(s.split())
    return s

def _to_tuple_normalized(d: Dict[str, Any], keys: List[str]) -> Tuple:
    """
    Like _to_tuple but applies _normalize to string values before building the tuple.
    Used for normalized F1 computation.
    """
    def _norm_val(v: Any) -> Any:
        return _normalize(v) if isinstance(v, str) else v
    return tuple(_norm_val(d.get(k, None)) for k in keys)

def _token_jaccard(a: str, b: str) -> float:
    """
    Token-level Jaccard similarity between two normalized strings.
    Used for soft F1 matching (threshold >= 0.8 counts as a match).
    """
    ta = set(_normalize(a).split()) if a else set()
    tb = set(_normalize(b).split()) if b else set()
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

def _extract_texts(entities: Iterable, keys: List[str]) -> List[str]:
    """
    Extract a textual representation from a list of entity dicts (or strings) using the provided keys. Falls back to the 'text' key or string conversion when a key is missing.
    Args:
        entities: An iterable of entities, which can be dictionaries or strings.
        keys: A list of keys to extract from each entity dictionary to form the text representation. If an entity is a string, it will be used directly. If a key is missing in a dictionary, it will fall back to the 'text' key or an empty string.
    Returns:
        List[str]: A list of text representations for the entities, constructed based on the specified keys and fallback logic.
    """
    texts: List[str] = []
    for e in entities:
        if isinstance(e, dict):
            parts: List[str] = []
            for k in keys:
                v = e.get(k)
                if v is None:
                    v = e.get("text", "")
                if v is None:
                    v = ""
                parts.append(str(v))
            # join non-empty parts with space
            texts.append(" ".join([p for p in parts if p]))
        else:
            texts.append(str(e))
    return texts

def _compute_bertscore_matrix(pred_texts: List[str], gold_texts: List[str], embedding_model: str, embedding_model_revision: str) -> Dict[str, float]:
    """
    Compute pairwise BERTScore between two lists of texts, perform a Hungarian matching to pair predictions with references, and return the average precision/recall/f1 across the matched pairs.
    Args:
        pred_texts: List of predicted text strings (e.g., entity texts or relation descriptions).
        gold_texts: List of gold standard text strings to compare against.
        embedding_model: The name of the embedding model to use for BERTScore (e.g., "bert-base-uncased").
        embedding_model_revision: The specific revision of the embedding model to use (e.g., "main" or a specific commit hash).
    Returns:
        Dict[str, float]: A dictionary containing the average BERTScore precision, recall, and F1 score for the best matching between predicted and gold texts.
    """
    # Defensive checks
    if not pred_texts or not gold_texts:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    # Build pairwise lists (pred,gold) for all combinations
    pair_preds: List[str] = []
    pair_refs: List[str] = []
    for p in pred_texts:
        for g in gold_texts:
            pair_preds.append(p)
            pair_refs.append(g)

    try:
        bertscore = _evaluate.load("bertscore")
        # Compute BERTScore for all pairs in a single batched call
        result = bertscore.compute(predictions=pair_preds, references=pair_refs, model_type=embedding_model, lang="en")
        p_list = result.get("precision", [])
        r_list = result.get("recall", [])
        f_list = result.get("f1", [])

        n_pred = len(pred_texts)
        n_gold = len(gold_texts)
        p_matrix = _np.array(p_list).reshape((n_pred, n_gold))
        r_matrix = _np.array(r_list).reshape((n_pred, n_gold))
        f_matrix = _np.array(f_list).reshape((n_pred, n_gold))

        # Hungarian assignment maximizing f1 (minimize cost = 1 - f1)
        row_ind, col_ind = _linear_sum_assignment(1.0 - f_matrix)
        if len(row_ind) == 0:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        matched_p = p_matrix[row_ind, col_ind]
        matched_r = r_matrix[row_ind, col_ind]
        matched_f = f_matrix[row_ind, col_ind]

        avg_p = float(_np.mean(matched_p)) if matched_p.size else 0.0
        avg_r = float(_np.mean(matched_r)) if matched_r.size else 0.0
        avg_f = float(_np.mean(matched_f)) if matched_f.size else 0.0
        return {"precision": avg_p, "recall": avg_r, "f1": avg_f}
    except Exception:
        # On any failure, return zeros and continue (do not blow up evaluation)
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

def entity_precision_recall_f1(gold_entities: List[Dict[str, Any]], pred_entities: List[Dict[str, Any]], match_keys: List[str], compute_bertscore: bool = False, bert_embedding_model: str = "bert-base-uncased", bert_embedding_model_revision: str = "main", compute_normalized_f1: bool = False, compute_soft_f1: bool = False) -> Dict[str, float]:
    """
    Compute precision, recall, F1 for entity sets using selected keys. Entities are considered a match if their specified keys match exactly. This allows for flexible evaluation based on different criteria (e.g., text only, text+type, etc.).
    Example:
        ```
        gold_entities = [{"text": "Aspirin", "type": "Chemical"}, {"text": "headache", "type": "Symptom"}]
        pred_entities = [{"text": "Aspirin", "type": "Chemical"}, {"text": "headache", "type": "Disease"}]
        match_keys = ["text", "type"] -> TP: 1 (Aspirin), FP: 1 (headache with wrong type), FN: 1 (headache with correct type)
        ```
    Args:
        gold_entities: List of dictionaries representing the gold standard entities.
        pred_entities: List of dictionaries representing the predicted entities.
        match_keys: List of keys to use for matching entities (e.g., ["text"], ["text", "type"], etc.).
        compute_bertscore: If True, compute BERTScore between predicted and gold entity texts.
        bert_embedding_model: The name of the embedding model to use for BERTScore.
        bert_embedding_model_revision: The specific revision of the embedding model to use.
        compute_normalized_f1: If True, also compute F1 after NFKC/lowercase/whitespace normalization. Results stored under key "normalized".
        compute_soft_f1: If True, also compute F1 using token-Jaccard soft matching (threshold >= 0.8 counts as a match). Results stored under key "soft".
    Returns:
        Dict[str, float]: A dictionary containing precision, recall, F1 score, and counts of true positives (tp), false positives (fp), and false negatives (fn). Optionally includes "normalized", "soft", and "bertscore" sub-dicts.
    """
    gold_set = set(_to_tuple(e, match_keys) for e in gold_entities)
    pred_set = set(_to_tuple(e, match_keys) for e in pred_entities)
    tp = len(gold_set & pred_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    out: Dict[str, Any] = {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}

    # Optionally compute Normalized F1 (NFKC + lowercase + whitespace normalization)
    if compute_normalized_f1:
        norm_gold_set = set(_to_tuple_normalized(e, match_keys) for e in gold_entities)
        norm_pred_set = set(_to_tuple_normalized(e, match_keys) for e in pred_entities)
        n_tp = len(norm_gold_set & norm_pred_set)
        n_fp = len(norm_pred_set - norm_gold_set)
        n_fn = len(norm_gold_set - norm_pred_set)
        n_p = n_tp / (n_tp + n_fp) if (n_tp + n_fp) > 0 else 0.0
        n_r = n_tp / (n_tp + n_fn) if (n_tp + n_fn) > 0 else 0.0
        n_f1 = 2 * n_p * n_r / (n_p + n_r) if (n_p + n_r) > 0 else 0.0
        out["normalized"] = {"precision": n_p, "recall": n_r, "f1": n_f1, "tp": n_tp, "fp": n_fp, "fn": n_fn}

    # Optionally compute Soft F1 (token-Jaccard >= 0.8 counts as a match, via Hungarian assignment)
    if compute_soft_f1:
        pred_texts_soft = _extract_texts(pred_entities, match_keys)
        gold_texts_soft = _extract_texts(gold_entities, match_keys)
        n_p_soft, n_g_soft = len(pred_texts_soft), len(gold_texts_soft)
        if n_p_soft == 0 and n_g_soft == 0:
            s_tp, s_fp, s_fn = 0, 0, 0
        elif n_p_soft == 0:
            s_tp, s_fp, s_fn = 0, 0, n_g_soft
        elif n_g_soft == 0:
            s_tp, s_fp, s_fn = 0, n_p_soft, 0
        else:
            jac_matrix = _np.zeros((n_p_soft, n_g_soft))
            for i, pt in enumerate(pred_texts_soft):
                for j, gt in enumerate(gold_texts_soft):
                    jac_matrix[i, j] = _token_jaccard(pt, gt)
            row_ind, col_ind = _linear_sum_assignment(1.0 - jac_matrix)
            s_tp = int(sum(1 for r, c in zip(row_ind, col_ind) if jac_matrix[r, c] >= 0.8))
            s_fp = n_p_soft - s_tp
            s_fn = n_g_soft - s_tp
        s_p = s_tp / (s_tp + s_fp) if (s_tp + s_fp) > 0 else 0.0
        s_r = s_tp / (s_tp + s_fn) if (s_tp + s_fn) > 0 else 0.0
        s_f1 = 2 * s_p * s_r / (s_p + s_r) if (s_p + s_r) > 0 else 0.0
        out["soft"] = {"precision": s_p, "recall": s_r, "f1": s_f1, "tp": s_tp, "fp": s_fp, "fn": s_fn}

    # Optionally compute BERTScore between predicted and gold entity texts
    if compute_bertscore:
        pred_texts = _extract_texts(pred_entities, match_keys)
        gold_texts = _extract_texts(gold_entities, match_keys)
        bert_scores = _compute_bertscore_matrix(pred_texts, gold_texts, bert_embedding_model, bert_embedding_model_revision)
        out["bertscore"] = bert_scores

    return out

def relation_precision_recall_f1(gold_relations: List[Dict[str, Any]], pred_relations: List[Dict[str, Any]], match_keys: List[str], compute_bertscore: bool = False, bert_embedding_model: str = "bert-base-uncased", bert_embedding_model_revision: str = "main", compute_normalized_f1: bool = False, compute_soft_f1: bool = False) -> Dict[str, float]:
    """
    Compute precision, recall, F1 for relation sets using selected keys. Relations are considered a match if their specified keys match exactly. This allows for flexible evaluation based on different criteria (e.g., type+entities).
    Example:
        ```
        gold_relations = [{"type": "treats", "chemical": "Aspirin", "disease": "headache"}]
        pred_relations = [{"type": "treats", "chemical": "Aspirin", "disease": "headache"}, {"type": "causes", "chemical": "Aspirin", "disease": "nausea"}]
        match_keys = ["type", "chemical", "disease"] -> TP: 1 (treats relation), FP: 1 (causes relation), FN: 0
        ```
    Args:
        gold_relations: List of dictionaries representing the gold standard relations.
        pred_relations: List of dictionaries representing the predicted relations.
        match_keys: List of keys to use for matching relations (e.g., ["type", "chemical", "disease"], etc.).
        compute_bertscore: If True, compute BERTScore between predicted and gold relation texts.
        bert_embedding_model: The name of the embedding model to use for BERTScore.
        bert_embedding_model_revision: The specific revision of the embedding model to use.
        compute_normalized_f1: If True, also compute F1 after NFKC/lowercase/whitespace normalization. Results stored under key "normalized".
        compute_soft_f1: If True, also compute F1 using token-Jaccard soft matching (threshold >= 0.8 counts as a match). Results stored under key "soft".
    Returns:
        Dict[str, float]: A dictionary containing precision, recall, F1 score, and counts of true positives (tp), false positives (fp), and false negatives (fn). Optionally includes "normalized", "soft", and "bertscore" sub-dicts.
    """
    return entity_precision_recall_f1(gold_relations, pred_relations, match_keys, compute_bertscore=compute_bertscore, bert_embedding_model=bert_embedding_model, bert_embedding_model_revision=bert_embedding_model_revision, compute_normalized_f1=compute_normalized_f1, compute_soft_f1=compute_soft_f1)

def span_micro_f1(gold_entities: List[Dict[str, Any]], pred_entities: List[Dict[str, Any]], span_keys: Optional[List[str]] = None, type_key: str = "type") -> Dict[str, float]:
    """
    Compute span-based micro-F1 (offset+length+type) for NER tasks. Entities are considered a match if their span (offset and length) and type match exactly. This is a common evaluation metric for NER tasks where correct identification of entity boundaries is crucial.
    Example:
        ```
        gold_entities = [{"text": "Aspirin", "type": "Chemical", "offset": 10, "length": 8}]
        pred_entities = [{"text": "Aspirin", "type": "Chemical", "offset": 10, "length": 8}, {"text": "headache", "type": "Symptom", "offset": 30, "length": 8}]
        span_keys = ["offset", "length"] -> TP: 1 (Aspirin), FP: 1 (headache), FN: 0
        ```
    Args:
        gold_entities: List of dictionaries representing the gold standard entities, each containing at least the keys specified in span_keys and type_key.
        pred_entities: List of dictionaries representing the predicted entities, each containing at least the keys specified in span_keys and type_key.
        span_keys: List of keys to use for defining the entity span (default is ["offset", "length"]). The combination of these keys along with the type_key will be used for matching.
        type_key: The key in the entity dictionaries that represents the entity type (default is "type"). This will be included in the matching criteria along with the span keys.
    Returns:
        Dict[str, float]: A dictionary containing precision, recall, F1 score, and counts of true positives (tp), false positives (fp), and false negatives (fn) based on span and type matching.
    """
    if span_keys is None:
        span_keys = ["offset", "length"]
    gold_set = set((_to_tuple(e, span_keys + [type_key])) for e in gold_entities)
    pred_set = set((_to_tuple(e, span_keys + [type_key])) for e in pred_entities)
    tp = len(gold_set & pred_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}

def aggregate_metrics(per_doc_metrics: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregate per-document metrics (micro average). This function sums up the true positives, false positives, and false negatives across all documents and then computes the overall precision, recall, and F1 score. This is a common approach for aggregating metrics in information extraction tasks to get an overall performance measure across a dataset.
    Example:
        ```
        per_doc_metrics = [
            {"precision": 1.0, "recall": 0.5, "f1": 0.67, "tp": 2, "fp": 0, "fn": 2},
            {"precision": 0.5, "recall": 1.0, "f1": 0.67, "tp": 1, "fp": 1, "fn": 0}
        ]
        total_tp = 3 (2 from doc1 + 1 from doc2)
        total_fp = 1 (0 from doc1 + 1 from doc2)
        total_fn = 2 (2 from doc1 + 0 from doc2)
        precision = 3 / (3 + 1) = 0.75
        recall = 3 / (3 + 2) = 0.6
        f1 = 2 * 0.75 * 0.6 / (0.75 + 0.6) = 0.67
        ```
    Args:
        per_doc_metrics: A list of dictionaries, each containing the precision, recall, F1 score, and counts of true positives (tp), false positives (fp), and false negatives (fn) for individual documents.
    Returns:
        Dict[str, float]: A dictionary containing the aggregated precision, recall, F1 score, and total counts of true positives (tp), false positives (fp), and false negatives (fn) across all documents.
    """
    total_tp = sum(m.get("tp", 0) for m in per_doc_metrics)
    total_fp = sum(m.get("fp", 0) for m in per_doc_metrics)
    total_fn = sum(m.get("fn", 0) for m in per_doc_metrics)
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    result: Dict[str, Any] = {"precision": precision, "recall": recall, "f1": f1, "tp": total_tp, "fp": total_fp, "fn": total_fn}

    # Aggregate optional BERTScore metrics (average across documents that include it)
    bs_precisions: List[float] = []
    bs_recalls: List[float] = []
    bs_f1s: List[float] = []
    for m in per_doc_metrics:
        bs = m.get("bertscore")
        if isinstance(bs, dict):
            if "precision" in bs:
                try:
                    bs_precisions.append(float(bs.get("precision", 0.0)))
                except Exception:
                    pass
            if "recall" in bs:
                try:
                    bs_recalls.append(float(bs.get("recall", 0.0)))
                except Exception:
                    pass
            if "f1" in bs:
                try:
                    bs_f1s.append(float(bs.get("f1", 0.0)))
                except Exception:
                    pass

    if bs_precisions:
        result["bertscore"] = {
            "precision": sum(bs_precisions) / len(bs_precisions),
            "recall": sum(bs_recalls) / len(bs_recalls) if bs_recalls else 0.0,
            "f1": sum(bs_f1s) / len(bs_f1s) if bs_f1s else 0.0,
        }

    # Aggregate Normalized F1 (micro, recomputed from summed tp/fp/fn)
    if any(isinstance(m.get("normalized"), dict) for m in per_doc_metrics):
        norm_tps = sum(m["normalized"]["tp"] for m in per_doc_metrics if isinstance(m.get("normalized"), dict))
        norm_fps = sum(m["normalized"]["fp"] for m in per_doc_metrics if isinstance(m.get("normalized"), dict))
        norm_fns = sum(m["normalized"]["fn"] for m in per_doc_metrics if isinstance(m.get("normalized"), dict))
        n_p = norm_tps / (norm_tps + norm_fps) if (norm_tps + norm_fps) > 0 else 0.0
        n_r = norm_tps / (norm_tps + norm_fns) if (norm_tps + norm_fns) > 0 else 0.0
        n_f = 2 * n_p * n_r / (n_p + n_r) if (n_p + n_r) > 0 else 0.0
        result["normalized"] = {"precision": n_p, "recall": n_r, "f1": n_f, "tp": norm_tps, "fp": norm_fps, "fn": norm_fns}

    # Aggregate Soft F1 (micro, recomputed from summed tp/fp/fn)
    if any(isinstance(m.get("soft"), dict) for m in per_doc_metrics):
        soft_tps = sum(m["soft"]["tp"] for m in per_doc_metrics if isinstance(m.get("soft"), dict))
        soft_fps = sum(m["soft"]["fp"] for m in per_doc_metrics if isinstance(m.get("soft"), dict))
        soft_fns = sum(m["soft"]["fn"] for m in per_doc_metrics if isinstance(m.get("soft"), dict))
        s_p = soft_tps / (soft_tps + soft_fps) if (soft_tps + soft_fps) > 0 else 0.0
        s_r = soft_tps / (soft_tps + soft_fns) if (soft_tps + soft_fns) > 0 else 0.0
        s_f = 2 * s_p * s_r / (s_p + s_r) if (s_p + s_r) > 0 else 0.0
        result["soft"] = {"precision": s_p, "recall": s_r, "f1": s_f, "tp": soft_tps, "fp": soft_fps, "fn": soft_fns}

    return result

def save_evaluation_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save evaluation results to a JSON file. This function takes the computed evaluation metrics and saves them in a structured JSON format for later analysis or reporting.
    Args:
        results: A dictionary containing the evaluation results, which may include precision, recall, F1 scores, and counts of true positives, false positives, and false negatives for different categories (e.g., entities, relations).
        output_path: The file path where the evaluation results should be saved as a JSON file.
    Raises:
        jsonschema.ValidationError: If the results dict does not conform to data/schemas/evaluation/evaluation_results.json.
    """
    # Validate against canonical schema before saving (schema path is relative to this file)
    _schema_path = Path(__file__).parent.parent.parent / "data" / "schemas" / "evaluation" / "evaluation_results.json"
    if _schema_path.exists():
        with open(_schema_path, encoding="utf-8") as _sf:
            _schema = json.load(_sf)
        jsonschema.Draft7Validator(_schema).validate(results)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def print_evaluation_summary(results: Dict[str, Any]) -> None:
    """
    Print evaluation summary in a readable format. This function formats the evaluation results and prints them to the console in a clear and concise manner, allowing for easy interpretation of the performance metrics.
    Args:
        results: A dictionary containing the evaluation results, which may include precision, recall, F1 scores, and counts of true positives, false positives, and false negatives for different categories (e.g., entities, relations).
    """
    # Initialize the logger
    logger = LogHandler.get_logger("scikg_extract")
    logger.info("\nEvaluation Summary:")
    
    for k, v in results.items():
        if not isinstance(v, dict):
            logger.info(f"{k:20s} | {v}")
            continue

        # Print main precision/recall/f1 and counts if available
        p = v.get("precision")
        r = v.get("recall")
        f = v.get("f1")
        tp = v.get("tp")
        fp = v.get("fp")
        fn = v.get("fn")

        if isinstance(p, (int, float)) and isinstance(r, (int, float)) and isinstance(f, (int, float)):
            if tp is not None and fp is not None and fn is not None:
                logger.info(f"{k:20s} | P: {p:.4f} R: {r:.4f} F1: {f:.4f} (TP: {tp}, FP: {fp}, FN: {fn})")
            else:
                logger.info(f"{k:20s} | P: {p:.4f} R: {r:.4f} F1: {f:.4f}")
        else:
            # Fallback display for non-numeric top-level values
            logger.info(f"{k:20s} | {v}")

        # If BERTScore was computed, display it as well
        bs = v.get("bertscore")
        if isinstance(bs, dict):
            bp = bs.get("precision", 0.0)
            br = bs.get("recall", 0.0)
            bf = bs.get("f1", 0.0)
            logger.info(f"{k:20s} | BERTScore P: {bp:.4f} R: {br:.4f} F1: {bf:.4f}")

        # If Normalized F1 was computed, display it as well
        nm = v.get("normalized")
        if isinstance(nm, dict):
            nm_p = nm.get("precision", 0.0)
            nm_r = nm.get("recall", 0.0)
            nm_f = nm.get("f1", 0.0)
            logger.info(f"{k:20s} | Normalized  P: {nm_p:.4f} R: {nm_r:.4f} F1: {nm_f:.4f}")

        # If Soft F1 was computed, display it as well
        sm = v.get("soft")
        if isinstance(sm, dict):
            sm_p = sm.get("precision", 0.0)
            sm_r = sm.get("recall", 0.0)
            sm_f = sm.get("f1", 0.0)
            logger.info(f"{k:20s} | Soft        P: {sm_p:.4f} R: {sm_r:.4f} F1: {sm_f:.4f}")