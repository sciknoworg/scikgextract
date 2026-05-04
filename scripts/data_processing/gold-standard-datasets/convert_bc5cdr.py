"""
Convert BC5CDR raw data (PubTator format) into processed JSON files with combined document text and structured entity/relation objects.
"""
# Python Imports
import json
import argparse
from typing import Any
from pathlib import Path

# SciKGExtract Utils Imports
from scikg_extract.utils.log_handler import LogHandler

def parse_pubtator(filepath: Path) -> list[dict[str, Any]]:
    """
    Parse a PubTator-formatted file into a list of document dicts.
    Args:
        filepath: Path to the PubTator .txt file.
    Returns:
        list[dict]: Documents with doc_id, title, abstract, raw entity lines, and raw relation lines.
    """
    documents: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            # Blank line signals end of document
            if not line:
                if current is not None:
                    documents.append(current)
                    current = None
                continue

            # Title line
            if "|t|" in line:
                pmid, _, title = line.partition("|t|")
                current = {
                    "doc_id": pmid.strip(),
                    "title": title,
                    "abstract": "",
                    "entity_lines": [],
                    "relation_lines": [],
                }
                continue

            # Abstract line
            if "|a|" in line and current is not None:
                _, _, abstract = line.partition("|a|")
                current["abstract"] = abstract
                continue

            # Tab-separated annotation lines
            if current is not None and "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 4 and parts[1] == "CID":
                    # Relation line: PMID\tCID\tChemicalID\tDiseaseID
                    current["relation_lines"].append(parts)
                elif len(parts) >= 6:
                    # Entity line: PMID\tStart\tEnd\tText\tType\tIdentifier
                    current["entity_lines"].append(parts)

    # Handle last document if file doesn't end with blank line
    if current is not None:
        documents.append(current)

    return documents

def build_document_text(doc: dict[str, Any]) -> str:
    """
    Reconstruct the full document text from title and abstract.
    Args:
        doc: Document dict with 'title' and 'abstract' keys.
    Returns:
        str: Combined text (title + abstract separated by newline).
    """
    return f"{doc['title']}\n{doc['abstract']}"

def extract_entities(entity_lines: list[list[str]]) -> list[dict[str, Any]]:
    """
    Convert raw PubTator entity lines into structured entity dicts.
    Args:
        entity_lines: List of tab-split entity lines [PMID, start, end, text, type, identifier].
    Returns:
        list[dict]: Entity dicts with text, type, identifier, offset, and length.
    """
    entities: list[dict[str, Any]] = []

    for parts in entity_lines:
        start = int(parts[1])
        end = int(parts[2])
        text = parts[3]
        entity_type = parts[4]
        identifier = parts[5] if len(parts) > 5 else ""

        entities.append(
            {
                "text": text,
                "type": entity_type,
                "identifier": identifier,
                "offset": start,
                "length": end - start,
            }
        )

    # Sort by offset
    entities.sort(key=lambda e: e["offset"])
    return entities

def extract_relations(relation_lines: list[list[str]]) -> list[dict[str, Any]]:
    """
    Convert raw PubTator CID relation lines into structured relation dicts.
    Args:
        relation_lines: List of tab-split relation lines [PMID, CID, ChemicalID, DiseaseID].
    Returns:
        list[dict]: Relation dicts with type, chemical, and disease.
    """
    relations: list[dict[str, Any]] = []

    for parts in relation_lines:
        relations.append(
            {
                "type": "CID",
                "chemical": parts[2],
                "disease": parts[3],
            }
        )

    return relations

def convert_split(filepath: Path) -> list[dict[str, Any]]:
    """
    Convert one split's raw PubTator file into the processed format.

    Args:
        filepath: Path to the PubTator .txt file for this split.

    Returns:
        list[dict]: Processed document dicts with doc_id, text, entities, and relations.
    """
    raw_docs = parse_pubtator(filepath)
    processed: list[dict[str, Any]] = []

    for doc in raw_docs:
        text = build_document_text(doc)
        entities = extract_entities(doc["entity_lines"])
        relations = extract_relations(doc["relation_lines"])

        processed.append(
            {
                "doc_id": doc["doc_id"],
                "text": text,
                "entities": entities,
                "relations": relations,
            }
        )

    return processed

def main():
    """
    Main function to convert BC5CDR raw PubTator data into processed JSON files for train, dev, and test splits.
    """
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Convert BC5CDR raw PubTator data to processed JSON.")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/gold-standard-datasets/BC5CDR/raw/CDR_Data/CDR_Data/CDR.Corpus.v010516"), help="Directory containing raw PubTator files.")
    parser.add_argument("--out-dir", type=Path, default=Path("data/gold-standard-datasets/BC5CDR/processed"), help="Output directory for processed JSON files.")

    # Parse arguments
    args = parser.parse_args()

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("convert_bc5cdr")
    logger.info("Starting BC5CDR data conversion script...")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    splits = {
        "CDR_TrainingSet.PubTator.txt": "train.json",
        "CDR_DevelopmentSet.PubTator.txt": "validation.json",
        "CDR_TestSet.PubTator.txt": "test.json",
    }

    for raw_name, out_name in splits.items():
        raw_path = args.raw_dir / raw_name
        if not raw_path.exists():
            logger.info(f"Skipping {raw_name}: file not found at {raw_path}")
            continue

        logger.info(f"Processing {raw_name}...")
        processed = convert_split(raw_path)

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
