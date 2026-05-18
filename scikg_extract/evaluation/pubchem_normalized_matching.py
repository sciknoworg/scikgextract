"""
PubChem CID-based normalized matching for chemical entity evaluation.

Implements the NormalizedMatcher interface using PubChem CID synonym/IUPAC/formula lookups. Provides both module-level functions (for direct script usage) and the PubChemMatcher class (for use with the runner and notebook pipelines).
"""
# Python Imports
import os
import re
from typing import Optional

# Third-Party Imports
from rapidfuzz import fuzz

# SciKG-Extract Imports
from scikg_extract.evaluation.normalized_matching import (
    NormalizedMatcher,
    _field_value,
    _normalize,
    _raw_value_matches_gold,
)

# Regex to extract a PubChem CID from a URL string
CID_URL_PATTERN = re.compile(r"pubchem\.ncbi\.nlm\.nih\.gov/compound/(\d+)")

# Folder names that are structural (never process-condition annotations)
_NON_PROC_NAMES = {
    "AtomicLimits Database", "cross-evaluation", "self-evaluation",
    "experimental-usecase", "ZnO", "IGZO",
    "two_judges", "three_judges",
}
_JUDGE_VARIANTS = {"two_judges", "three_judges"}
_EVAL_TYPES = {"cross-evaluation", "self-evaluation"}


# ---------------------------------------------------------------------------
# CID extraction from sameAs fields
# ---------------------------------------------------------------------------

def _extract_cids(same_as_val) -> list[str]:
    """
    Return all PubChem CID strings found in a sameAs field.

    Args:
        same_as_val: A single URL string or a list of URL strings.
    Returns:
        List of CID strings (e.g. ["11185", "101667988"]).
    """
    if not same_as_val:
        return []
    if isinstance(same_as_val, str):
        same_as_val = [same_as_val]
    cids = []
    for url in same_as_val:
        m = CID_URL_PATTERN.search(str(url))
        if m:
            cids.append(m.group(1))
    return cids

def _field_cids(field_val) -> list[str]:
    """
    Given a chemical field value (plain string or {"value": ..., "sameAs": [...]}) return all CIDs from its sameAs list. A plain string yields an empty list (the value was not normalized).

    Args:
        field_val: The raw field value from the extraction JSON.
    Returns:
        List of CID strings.
    """
    if isinstance(field_val, dict):
        return _extract_cids(field_val.get("sameAs", []))
    return []

# ---------------------------------------------------------------------------
# Synonym matching
# ---------------------------------------------------------------------------

def _cid_matches_gold(cid: str, gold_str: str, cid_repr: dict, threshold: int = 85) -> bool:
    """
    Return True if gold_str matches any representation of the given CID.

    Checks (in order):
      1. Exact normalized match against IUPAC name, molecular formula, or any synonym.
      2. Fuzzy token_set_ratio >= threshold against IUPAC name or the first 200 synonyms.

    Args:
        cid: PubChem CID string.
        gold_str: Gold chemical name string (from folder annotation).
        cid_repr: CID representations dictionary loaded from pubchem_cid_representations.json.
        threshold: Minimum rapidfuzz token_set_ratio score (0–100) to accept a fuzzy match.
    Returns:
        True if the gold string matches, False otherwise.
    """
    if not cid or not gold_str:
        return False
    entry = cid_repr.get(cid)
    if not entry:
        return False

    gold_norm = _normalize(gold_str)
    iupac = entry.get("iupac_name") or ""
    mf = entry.get("molecular_formula") or ""
    synonyms: list[str] = entry.get("synonyms") or []

    # Exact normalized matches
    if iupac and _normalize(iupac) == gold_norm:
        return True
    if mf and _normalize(mf) == gold_norm:
        return True
    for syn in synonyms:
        if _normalize(syn) == gold_norm:
            return True

    # Fuzzy fallback (cap synonym list for speed)
    candidates = ([iupac] if iupac else []) + synonyms[:200]
    for cand in candidates:
        if fuzz.token_set_ratio(gold_norm, _normalize(cand)) >= threshold:
            return True

    return False

def _any_cid_matches_gold(cids: list[str], gold_str: str, cid_repr: dict, threshold: int = 85) -> bool:
    """Return True if ANY CID in cids matches gold_str."""
    return any(_cid_matches_gold(cid, gold_str, cid_repr, threshold) for cid in cids)

def _pred_matches_gold(cids: list[str], raw_val: Optional[str], gold_str: str, cid_repr: dict, threshold: int = 85) -> bool:
    """
    Return True if a prediction matches gold_str via either:
      1. CID-based synonym/IUPAC/formula matching, or
      2. Direct raw extracted value matching.

    Args:
        cids: PubChem CIDs from the prediction's sameAs URLs.
        raw_val: Raw extracted string value from the prediction.
        gold_str: Gold chemical name string.
        cid_repr: CID representations dictionary.
        threshold: Fuzzy match threshold.
    Returns:
        True if either matching path succeeds.
    """
    if cids and _any_cid_matches_gold(cids, gold_str, cid_repr, threshold):
        return True
    if raw_val and _raw_value_matches_gold(raw_val, gold_str, threshold):
        return True
    return False

# ---------------------------------------------------------------------------
# Per-process metric computation
# ---------------------------------------------------------------------------

def _compute_metrics(gold_strs: list[str], pred_cid_lists: list[list[str]], cid_repr: dict, threshold: int = 85, pred_raw_values: Optional[list[Optional[str]]] = None) -> dict:
    """
    Set-based P/R/F1 counts for one chemical category within one process.

    Matching is greedy: for each predicted chemical, we check if it matches any still-unmatched gold string via CID-based lookup OR raw extracted value. Each gold string can only contribute one TP.

    Args:
        gold_strs: Gold chemical name strings for this category/process.
        pred_cid_lists: One list of CIDs per predicted chemical slot.
        cid_repr: CID representations dictionary.
        threshold: Fuzzy match threshold.
        pred_raw_values: Parallel list of raw extracted value strings (one per
            prediction slot). Used as a fallback when CID matching fails.
    Returns:
        {"tp": int, "fp": int, "fn": int}
    """
    remaining_gold = list(gold_strs)
    tp = 0
    fp = 0
    raw_vals = pred_raw_values or [None] * len(pred_cid_lists)

    for pred_cids, raw_val in zip(pred_cid_lists, raw_vals):
        matched = False
        for i, gold_str in enumerate(remaining_gold):
            if _pred_matches_gold(pred_cids, raw_val, gold_str, cid_repr, threshold):
                tp += 1
                remaining_gold.pop(i)
                matched = True
                break
        if not matched:
            fp += 1

    fn = len(remaining_gold)
    return {"tp": tp, "fp": fp, "fn": fn}

def _compute_metrics_any_match(gold_strs: list[str], pred_cid_lists: list[list[str]], cid_repr: dict, threshold: int = 85, pred_raw_values: Optional[list[Optional[str]]] = None) -> dict:
    """
    Gold-coverage metric: a gold string is a TP if ANY prediction matches it via CID-based lookup OR raw extracted value, regardless of how many other predictions exist. Extra predictions that match no gold are counted as FPs.

    This is appropriate when the gold annotation is not exhaustive (e.g. only the primary precursor is annotated but models may correctly extract more).

    TP = number of gold strings matched by at least one prediction.
    FN = number of gold strings not matched by any prediction.
    FP = number of predictions that match NO gold string.

    Args:
        gold_strs: Gold chemical name strings for this category/process.
        pred_cid_lists: One list of CIDs per predicted chemical slot.
        cid_repr: CID representations dictionary.
        threshold: Fuzzy match threshold.
        pred_raw_values: Parallel list of raw extracted value strings.
    Returns:
        {"tp": int, "fp": int, "fn": int}
    """
    matched_gold: set[int] = set()
    matched_pred: set[int] = set()
    raw_vals = pred_raw_values or [None] * len(pred_cid_lists)

    for pred_idx, (pred_cids, raw_val) in enumerate(zip(pred_cid_lists, raw_vals)):
        for gold_idx, gold_str in enumerate(gold_strs):
            if gold_idx in matched_gold:
                continue
            if _pred_matches_gold(pred_cids, raw_val, gold_str, cid_repr, threshold):
                matched_gold.add(gold_idx)
                matched_pred.add(pred_idx)

    tp = len(matched_gold)
    fn = len(gold_strs) - tp
    fp = sum(
        1 for pred_idx in range(len(pred_cid_lists))
        if pred_idx not in matched_pred
    )
    return {"tp": tp, "fp": fp, "fn": fn}

# ---------------------------------------------------------------------------
# Folder path parsing
# ---------------------------------------------------------------------------

def _parse_folder_annotations(root: str) -> tuple[Optional[str], list[str], Optional[str], Optional[str]]:
    """
    Parse the extraction folder path to extract the gold material, chemical annotations, the judge-variant (experiment3), and evaluation type (experiment4).

    Supported layouts:

      Standard (experiments 1, 2):
        .../experimental-usecase/{ZnO|IGZO}/[AtomicLimits Database/[cross-evaluation/]]
            {PROCESS-COND}/{LLM}

      With evaluation type (experiment 4):
        .../experimental-usecase/{ZnO|IGZO}/{cross-evaluation|self-evaluation}/{PROCESS-COND}/{LLM}
        .../experimental-usecase/{ZnO|IGZO}/AtomicLimits Database/
            {cross-evaluation|self-evaluation}/{PROCESS-COND}/{LLM}

      With judge variant (experiment 3):
        .../experimental-usecase/{ZnO|IGZO}/{two_judges|three_judges}/{PROCESS-COND}/{LLM}

    In all cases the LLM model folder is the leaf (parts[-1]) and the process-condition folder is directly above it (parts[-2]). Annotations are produced by splitting the process-condition folder name on " - ".

    ZnO  (e.g. "ZnEt2 - H2O"):
      annotations[0]    → single precursor
      annotations[1:]   → co-reactant(s)

    IGZO (e.g. "InMe3 - GaMe3 - ZnEt2 - O3"):
      annotations[:-1]  → all precursors (In / Ga / Zn sources)
      annotations[-1]   → co-reactant

    Args:
        root: Current directory path from os.walk.

    Returns:
        (material, annotations, judges, evaluation_type)
        where judges is e.g. "two_judges" or None,
        and evaluation_type is "cross-evaluation", "self-evaluation", or None.
    """
    parts = os.path.normpath(root).split(os.sep)

    # Find material by searching backward through path components
    material = next((p for p in reversed(parts) if p in ("ZnO", "IGZO")), None)
    if not material:
        return None, [], None, None

    # Process-condition folder is always immediately above the LLM model folder
    proc_cond = parts[-2]
    if proc_cond in _NON_PROC_NAMES:
        return None, [], None, None

    # Detect judge-variant OR evaluation-type folder one level above proc_cond
    parent = parts[-3] if len(parts) >= 3 else ""
    judges = parent if parent in _JUDGE_VARIANTS else None
    evaluation_type = parent if parent in _EVAL_TYPES else None

    annotations = [a.strip() for a in proc_cond.split(" - ") if a.strip()]
    return material, annotations, judges, evaluation_type

# ---------------------------------------------------------------------------
# PubChem matcher class
# ---------------------------------------------------------------------------

class PubChemMatcher(NormalizedMatcher):
    """
    NormalizedMatcher implementation backed by PubChem CID synonym lookups.

    Implements the two abstract methods required by NormalizedMatcher:
      - field_identifiers(): extracts PubChem CIDs from a field's sameAs URLs.
      - id_matches_gold(): matches a CID against a gold string via exact/fuzzy
        synonym, IUPAC name, and molecular formula lookup.

    The inherited pred_matches_gold(), compute_metrics(), and compute_metrics_any_match() use these two methods automatically.
    """

    def field_identifiers(self, field_val) -> list[str]:
        """Extract PubChem CIDs from the field's sameAs URLs."""
        return _field_cids(field_val)

    def id_matches_gold(self, identifier: str, gold_str: str, repr_dict: dict, threshold: int = 85) -> bool:
        """Return True if the PubChem CID matches the gold string."""
        return _cid_matches_gold(identifier, gold_str, repr_dict, threshold)