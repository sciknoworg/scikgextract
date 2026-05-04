"""
Convert PolyIE raw data (BIO-tagged tokens with relation indices) into processed JSON files with reconstructed text and structured entity relation objects.
"""
# Python Imports
import json
import argparse
from typing import Any
from pathlib import Path

# SciKGExtract Utils Imports
from scikg_extract.utils.log_handler import LogHandler

# BIO tag prefix -> entity category key
ENTITY_TAG_MAP = {
    "CN": "chemicalNames",
    "PN": "propertyNames",
    "PV": "propertyValues",
    "Condition": "conditions",
}

def extract_entities_from_bio(tokens: list[str], labels: list[str]) -> dict[str, list[str]]:
    """
    Convert BIO-tagged token/label sequences into grouped entity strings.
    Args:
        tokens: List of token strings for a sentence.
        labels: Corresponding list of BIO labels for each token.
    Returns:
        dict: A dictionary mapping entity categories to lists of extracted entity strings.
    """
    entities: dict[str, list[str]] = {v: [] for v in ENTITY_TAG_MAP.values()}

    current_tokens: list[str] = []
    current_type: str | None = None

    def flush() -> None:
        if current_type and current_tokens:
            key = ENTITY_TAG_MAP.get(current_type)
            if key:
                entities[key].append(" ".join(current_tokens))

    for tok, lab in zip(tokens, labels):
        if lab.startswith("B-"):
            flush()
            tag_type = lab[2:]
            current_type = tag_type
            current_tokens = [tok]
        elif lab.startswith("I-") and current_type == lab[2:]:
            current_tokens.append(tok)
        else:
            flush()
            current_type = None
            current_tokens = []

    flush()

    # Deduplicate while preserving order
    for key in entities:
        seen: set[str] = set()
        deduped: list[str] = []
        for e in entities[key]:
            if e not in seen:
                seen.add(e)
                deduped.append(e)
        entities[key] = deduped

    return entities

def span_to_text(tokens: list[str], span: list[int]) -> str:
    """
    Extract text from a token span given as [start, end) indices.
    Args:
        tokens: List of token strings for a sentence.
        span: List of token indices representing the span (e.g., [2, 5] for tokens[2:5]).
    Returns:
        str: The text corresponding to the token span, joined by spaces.
    """
    start, end = span[0], span[-1]
    return " ".join(tokens[start:end])

def extract_relations(tokens: list[str], raw_relations: list[list[list[int]]]) -> list[dict[str, Any]]:
    """
    Convert raw relation index triples/quads into structured dicts. Each relation is expected to have at least chemical and property spans, with optional value and condition spans.
    Args:
        tokens: List of token strings for a sentence.
        raw_relations: List of relations, where each relation is a list of token index spans (e.g., [[0,1], [3,4], [5,6], [7,8]]).
    Returns:
        list[dict]: A list of relation dictionaries with keys 'chemicalName', 'propertyName', 'propertyValue', and 'condition'.
    """
    relations: list[dict[str, Any]] = []
    for rel in raw_relations:
        if len(rel) < 2:
            continue
        entry: dict[str, Any] = {
            "chemicalName": span_to_text(tokens, rel[0]),
            "propertyName": span_to_text(tokens, rel[1]),
        }
        if len(rel) >= 3:
            entry["propertyValue"] = span_to_text(tokens, rel[2])
        else:
            entry["propertyValue"] = None
        if len(rel) >= 4:
            entry["condition"] = span_to_text(tokens, rel[3])
        else:
            entry["condition"] = None
        relations.append(entry)
    return relations

def convert_split(raw_data: dict[str, list]) -> list[dict[str, Any]]:
    """
    Convert one split's raw data into the processed format.
    Args:
        raw_data: A dictionary containing 'text', 'label', and 'relation' lists for the split.
    Returns:
        list[dict]: A list of document dictionaries, each containing sentences with text, entities, and relations.
    """
    documents: list[dict[str, Any]] = []
    num_docs = len(raw_data["text"])

    for doc_idx in range(num_docs):
        doc_texts = raw_data["text"][doc_idx]
        doc_labels = raw_data["label"][doc_idx]
        doc_relations = raw_data["relation"][doc_idx]

        sentences: list[dict[str, Any]] = []
        for sent_idx in range(len(doc_texts)):
            tokens = doc_texts[sent_idx]
            labels = doc_labels[sent_idx]
            rels_raw = doc_relations[sent_idx]

            text = " ".join(tokens)
            entities = extract_entities_from_bio(tokens, labels)
            relations = extract_relations(tokens, rels_raw)

            sentences.append(
                {
                    "sent_id": sent_idx,
                    "text": text,
                    "entities": entities,
                    "relations": relations,
                }
            )

        documents.append({"doc_id": doc_idx, "sentences": sentences})

    return documents

def main():
    """
    Main function to convert PolyIE raw BIO-tagged data into processed JSON files for train, validation, and test splits.
    """
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Convert PolyIE raw BIO-tagged data to processed JSON.")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/gold-standard-datasets/PolyIE/raw"), help="Directory containing raw split files.")
    parser.add_argument("--out-dir", type=Path, default=Path("data/gold-standard-datasets/PolyIE/processed"), help="Output directory for processed JSON files.")
    
    # Parse arguments
    args = parser.parse_args()

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("convert_polyie")
    logger.info("Starting PolyIE data conversion script...")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    splits = {
        "train_split.txt": "train.json",
        "validation_split.txt": "validation.json",
        "test_split.txt": "test.json",
    }

    for raw_name, out_name in splits.items():
        raw_path = args.raw_dir / raw_name
        if not raw_path.exists():
            logger.info(f"Skipping {raw_name}: file not found at {raw_path}")
            continue

        logger.info(f"Processing {raw_name}...")
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        documents = convert_split(raw_data)

        out_path = args.out_dir / out_name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)

        # Print summary stats
        total_sents = sum(len(d["sentences"]) for d in documents)
        total_rels = sum(
            len(s["relations"]) for d in documents for s in d["sentences"]
        )
        total_ents = sum(
            sum(len(v) for v in s["entities"].values())
            for d in documents
            for s in d["sentences"]
        )
        logger.info(f"  -> {out_path}: {len(documents)} docs, {total_sents} sentences, {total_ents} entities, {total_rels} relations")

    logger.info("Done.")

if __name__ == "__main__":
    main()
