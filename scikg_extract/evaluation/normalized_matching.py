"""
Base protocol and shared utilities for external-source normalized matching.

Defines the NormalizedMatcher abstract interface that all source-specific matchers (PubChem, ChEBI, Wikidata, etc.) must implement, and provides source-agnostic utilities that every implementation can reuse.

Adding a new source:
    1. Create scikg_extract/evaluation/<source>_normalized_matching.py
    2. Subclass NormalizedMatcher and implement field_identifiers() and id_matches_gold()
    3. The inherited pred_matches_gold(), compute_metrics(), compute_metrics_any_match()
       work automatically via those two abstract methods.
"""
# Python Imports
from abc import ABC, abstractmethod
from typing import Optional

# Third-Party Imports
from rapidfuzz import fuzz

# SciKG-Extract Imports — _normalize re-exported here for convenience
from scikg_extract.evaluation.metrics import _normalize

__all__ = [
    "NormalizedMatcher",
    "_normalize",
    "_field_value",
    "_raw_value_matches_gold",
]


# ---------------------------------------------------------------------------
# Source-agnostic utilities
# ---------------------------------------------------------------------------

def _field_value(field_val) -> Optional[str]:
    """
    Extract the raw string value from a chemical field. Handles both plain strings (unnormalized extractions) and {"value": ..., "sameAs": [...]} dicts (normalized extractions).

    Args:
        field_val: The raw field value from the extraction JSON.
    Returns:
        The extracted string, or None if field is absent/empty.
    """
    if isinstance(field_val, dict):
        return field_val.get("value") or None
    if isinstance(field_val, str) and field_val:
        return field_val
    return None

def _raw_value_matches_gold(raw_val: str, gold_str: str, threshold: int = 85) -> bool:
    """
    Return True if the raw extracted string matches the gold string.

    Checks (in order):
      1. Exact normalized match (NFKC + lower + whitespace collapse).
      2. Fuzzy token_set_ratio >= threshold.

    Args:
        raw_val: The model's raw extracted value string.
        gold_str: Gold chemical name string.
        threshold: Minimum rapidfuzz score (0–100) to accept a fuzzy match.
    Returns:
        True if the raw value matches the gold string.
    """
    if not raw_val or not gold_str:
        return False
    if _normalize(raw_val) == _normalize(gold_str):
        return True
    return fuzz.token_set_ratio(_normalize(raw_val), _normalize(gold_str)) >= threshold

# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class NormalizedMatcher(ABC):
    """
    Abstract base class for external-source normalized chemical name matching.

    Subclasses implement two abstract methods that are source-specific:
      - field_identifiers(): extract KB identifiers (CIDs, ChEBI IDs, …) from a field
      - id_matches_gold(): decide whether a single identifier matches a gold string

    All higher-level logic (pred_matches_gold, compute_metrics, etc.) is inherited and works automatically through those two methods.
    """

    @abstractmethod
    def field_identifiers(self, field_val) -> list[str]:
        """
        Extract source-specific identifiers from a field's sameAs list.

        Args:
            field_val: Raw field value (str or {"value": ..., "sameAs": [...]}).
        Returns:
            List of identifier strings (e.g. PubChem CIDs, ChEBI IDs).
        """

    @abstractmethod
    def id_matches_gold(self, identifier: str, gold_str: str, repr_dict: dict, threshold: int = 85) -> bool:
        """
        Return True if a single source identifier matches the gold string.

        Args:
            identifier: Source-specific identifier (e.g. a PubChem CID string).
            gold_str: Gold chemical name string.
            repr_dict: Source representations dictionary (structure is source-defined).
            threshold: Fuzzy match threshold (0–100).
        """

    def field_value(self, field_val) -> Optional[str]:
        """Extract raw string value from a field. Override for non-standard schemas."""
        return _field_value(field_val)

    def raw_value_matches_gold(self, raw_val: str, gold_str: str, threshold: int = 85) -> bool:
        """Check raw string match. Override for source-specific fuzzy logic."""
        return _raw_value_matches_gold(raw_val, gold_str, threshold)

    def pred_matches_gold(self, identifiers: list[str], raw_val: Optional[str], gold_str: str, repr_dict: dict, threshold: int = 85) -> bool:
        """
        Return True if a prediction matches gold_str via identifier lookup OR raw value.

        Args:
            identifiers: Source-specific identifiers from the prediction's sameAs URLs.
            raw_val: Raw extracted string value from the prediction.
            gold_str: Gold chemical name string.
            repr_dict: Source representations dictionary.
            threshold: Fuzzy match threshold.
        """
        if identifiers and any(
            self.id_matches_gold(i, gold_str, repr_dict, threshold) for i in identifiers
        ):
            return True
        if raw_val and self.raw_value_matches_gold(raw_val, gold_str, threshold):
            return True
        return False

    def compute_metrics(self, gold_strs: list[str], pred_id_lists: list[list[str]], repr_dict: dict, threshold: int = 85, pred_raw_values: Optional[list[Optional[str]]] = None,
    ) -> dict:
        """
        Set-based P/R/F1 counts (greedy matching).

        Each gold string can only contribute one TP. For each predicted chemical, checks if it matches any still-unmatched gold string.

        Args:
            gold_strs: Gold chemical name strings.
            pred_id_lists: One list of identifiers per predicted chemical slot.
            repr_dict: Source representations dictionary.
            threshold: Fuzzy match threshold.
            pred_raw_values: Parallel list of raw extracted value strings.
        Returns:
            {"tp": int, "fp": int, "fn": int}
        """
        remaining_gold = list(gold_strs)
        tp = fp = 0
        raw_vals = pred_raw_values or [None] * len(pred_id_lists)
        for pred_ids, raw_val in zip(pred_id_lists, raw_vals):
            matched = False
            for i, gold_str in enumerate(remaining_gold):
                if self.pred_matches_gold(pred_ids, raw_val, gold_str, repr_dict, threshold):
                    tp += 1
                    remaining_gold.pop(i)
                    matched = True
                    break
            if not matched:
                fp += 1
        return {"tp": tp, "fp": fp, "fn": len(remaining_gold)}

    def compute_metrics_any_match(self, gold_strs: list[str], pred_id_lists: list[list[str]], repr_dict: dict, threshold: int = 85, pred_raw_values: Optional[list[Optional[str]]] = None,
    ) -> dict:
        """
        Gold-coverage metric: a gold string is a TP if ANY prediction matches it.

        Appropriate when gold annotations are not exhaustive (e.g. only the primary precursor is annotated but models may correctly extract more).

        Args:
            gold_strs: Gold chemical name strings.
            pred_id_lists: One list of identifiers per predicted chemical slot.
            repr_dict: Source representations dictionary.
            threshold: Fuzzy match threshold.
            pred_raw_values: Parallel list of raw extracted value strings.
        Returns:
            {"tp": int, "fp": int, "fn": int}
        """
        matched_gold: set[int] = set()
        matched_pred: set[int] = set()
        raw_vals = pred_raw_values or [None] * len(pred_id_lists)
        for pred_idx, (pred_ids, raw_val) in enumerate(zip(pred_id_lists, raw_vals)):
            for gold_idx, gold_str in enumerate(gold_strs):
                if gold_idx in matched_gold:
                    continue
                if self.pred_matches_gold(pred_ids, raw_val, gold_str, repr_dict, threshold):
                    matched_gold.add(gold_idx)
                    matched_pred.add(pred_idx)
        tp = len(matched_gold)
        fn = len(gold_strs) - tp
        fp = sum(1 for i in range(len(pred_id_lists)) if i not in matched_pred)
        return {"tp": tp, "fp": fp, "fn": fn}