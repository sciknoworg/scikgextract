"""
Convert BioRED raw data (BioC JSON format) into processed JSON files with combined document text and structured entity/relation objects.
"""
# Python Imports
import json
import argparse
from typing import Any
from pathlib import Path

# SciKGExtract Utils Imports
from scikg_extract.utils.log_handler import LogHandler

def extract_entities(passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Collect all entity annotations from document passages, deduplicated by (identifier, offset, length).
    Args:
        passages: List of passage dicts from the BioC document.
    Returns:
        list[dict]: Deduplicated entity dicts with text, type, identifier, offset, and length.
    """
    entities: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()

    for passage in passages:
        for ann in passage.get("annotations", []):
            identifier = ann["infons"].get("identifier", "")
            entity_type = ann["infons"].get("type", "")
            text = ann.get("text", "")

            for loc in ann.get("locations", []):
                offset = loc["offset"]
                length = loc["length"]
                key = (identifier, offset, length)
                if key in seen:
                    continue
                seen.add(key)
                entities.append(
                    {
                        "text": text,
                        "type": entity_type,
                        "identifier": identifier,
                        "offset": offset,
                        "length": length,
                    }
                )

    # Sort by offset for readability
    entities.sort(key=lambda e: e["offset"])
    return entities

def extract_relations(raw_relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert raw BioC relation entries into structured relation dicts.
    Args:
        raw_relations: List of relation dicts from the BioC document, each with 'infons' containing entity1, entity2, type, and novel.
    Returns:
        list[dict]: Relation dicts with type, entity1, entity2, and novel (bool).
    """
    relations: list[dict[str, Any]] = []
    for rel in raw_relations:
        infons = rel.get("infons", {})
        relations.append(
            {
                "type": infons.get("type", ""),
                "entity1": infons.get("entity1", ""),
                "entity2": infons.get("entity2", ""),
                "novel": infons.get("novel", "No") == "Novel",
            }
        )
    return relations

def build_document_text(passages: list[dict[str, Any]]) -> str:
    """
    Reconstruct the full document text from passages using their offsets.
    Args:
        passages: List of passage dicts with 'offset' and 'text'.
    Returns:
        str: Combined document text (title + abstract).
    """
    sorted_passages = sorted(passages, key=lambda p: p["offset"])
    parts: list[str] = []
    for p in sorted_passages:
        parts.append(p.get("text", ""))
    return "\n".join(parts)

def convert_split(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Convert one split's raw BioC JSON data into the processed format.
    Args:
        raw_data: Parsed BioC JSON dict with a 'documents' list.
    Returns:
        list[dict]: Processed document dicts with doc_id, text, entities, and relations.
    """
    processed: list[dict[str, Any]] = []

    for doc in raw_data.get("documents", []):
        doc_id = doc.get("id", "")
        passages = doc.get("passages", [])

        text = build_document_text(passages)
        entities = extract_entities(passages)
        relations = extract_relations(doc.get("relations", []))

        processed.append(
            {
                "doc_id": doc_id,
                "text": text,
                "entities": entities,
                "relations": relations,
            }
        )

    return processed

def main():
    """
    Main function to convert BioRED raw BioC JSON data into processed JSON files for train, dev, and test splits.
    """
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Convert BioRED raw BioC JSON data to processed JSON.")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/gold-standard-datasets/BioRED/raw"), help="Directory containing raw BioC JSON files.")
    parser.add_argument("--out-dir", type=Path, default=Path("data/gold-standard-datasets/BioRED/processed"), help="Output directory for processed JSON files.")

    # Parse arguments
    args = parser.parse_args()

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("convert_biored")
    logger.info("Starting BioRED data conversion script...")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    splits = {
        "Train.BioC.JSON": "train.json",
        "Dev.BioC.JSON": "validation.json",
        "Test.BioC.JSON": "test.json",
    }

    for raw_name, out_name in splits.items():
        raw_path = args.raw_dir / raw_name
        if not raw_path.exists():
            logger.info(f"Skipping {raw_name}: file not found at {raw_path}")
            continue

        logger.info(f"Processing {raw_name}...")
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        processed = convert_split(raw_data)

        out_path = args.out_dir / out_name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(processed, f, indent=2, ensure_ascii=False)

        # Print summary stats
        total_ents = sum(len(d["entities"]) for d in processed)
        total_rels = sum(len(d["relations"]) for d in processed)
        logger.info(f"  -> {out_path}: {len(processed)} docs, {total_ents} entities, {total_rels} relations")

    logger.info("Done.")

if __name__ == "__main__":
    main()
