"""
Convert PcMSP raw data (sentence-level vertex/edge graphs) into processed JSON files with reconstructed text and structured entity/relation objects.
"""
# Python Imports
import json
import argparse
from typing import Any
from pathlib import Path

# SciKGExtract Utils Imports
from scikg_extract.utils.log_handler import LogHandler

# Entity types that carry a subtype qualifier
MATERIAL_TYPES = {"Material-target", "Material-recipe", "Material-intermedium", "Material-others"}
PROPERTY_TYPES = {"Property-temperature", "Property-time", "Property-pressure", "Property-rate"}

# Simple entity types (stored as plain strings)
SIMPLE_ENTITY_MAP = {
    "Operation": "operations",
    "Descriptor": "descriptors",
    "Value": "values",
    "Device": "devices",
    "Brand": "brands",
}

def extract_entities(vertex_set: list[dict[str, Any]]) -> dict[str, list]:
    """
    Group vertices into typed entity lists.
    Args:
        vertex_set: List of vertex dicts from the raw data, each with 'lexicalInput' (text), 'kbID' (entity type), and 'tokenpositions'.
    Returns:
        dict: Entity categories mapped to lists of entity strings or typed objects.
    """
    entities: dict[str, list] = {
        "materials": [],
        "operations": [],
        "descriptors": [],
        "values": [],
        "properties": [],
        "devices": [],
        "brands": [],
    }

    for v in vertex_set:
        text = v["lexicalInput"]
        kb_id = v["kbID"]

        if kb_id in MATERIAL_TYPES:
            entities["materials"].append({"text": text, "subtype": kb_id})
        elif kb_id in PROPERTY_TYPES:
            entities["properties"].append({"text": text, "subtype": kb_id})
        elif kb_id in SIMPLE_ENTITY_MAP:
            entities[SIMPLE_ENTITY_MAP[kb_id]].append(text)

    # Deduplicate simple entity lists while preserving order
    for key in ["operations", "descriptors", "values", "devices", "brands"]:
        seen: set[str] = set()
        deduped: list[str] = []
        for e in entities[key]:
            if e not in seen:
                seen.add(e)
                deduped.append(e)
        entities[key] = deduped

    # Deduplicate typed entity lists (materials, properties) by (text, subtype)
    for key in ["materials", "properties"]:
        seen_typed: set[tuple[str, str]] = set()
        deduped_typed: list[dict] = []
        for e in entities[key]:
            pair = (e["text"], e["subtype"])
            if pair not in seen_typed:
                seen_typed.add(pair)
                deduped_typed.append(e)
        entities[key] = deduped_typed

    return entities

def build_tokpos_to_text(vertex_set: list[dict[str, Any]]) -> dict[tuple[int, ...], str]:
    """
    Build a lookup from frozen token-position tuples to lexical text.
    Args:
        vertex_set: List of vertex dicts from the raw data.
    Returns:
        dict: Mapping from tuple of token positions to the vertex's lexicalInput.
    """
    lookup: dict[tuple[int, ...], str] = {}
    for v in vertex_set:
        key = tuple(v["tokenpositions"])
        lookup[key] = v["lexicalInput"]
    return lookup

def extract_relations(edge_set: list[dict[str, Any]], tokpos_lookup: dict[tuple[int, ...], str]) -> list[dict[str, str]]:
    """
    Convert raw edges into structured relation dicts.
    Args:
        edge_set: List of edge dicts, each with 'kbID' (relation type), 'left' (source token positions), and 'right' (target token positions).
        tokpos_lookup: Mapping from token position tuples to entity text.
    Returns:
        list[dict]: Relations with 'type', 'source', and 'target' keys.
    """
    relations: list[dict[str, str]] = []
    for e in edge_set:
        left_key = tuple(e["left"])
        right_key = tuple(e["right"])
        source = tokpos_lookup.get(left_key)
        target = tokpos_lookup.get(right_key)
        if source is None or target is None:
            continue
        relations.append(
            {
                "type": e["kbID"],
                "source": source,
                "target": target,
            }
        )
    return relations

def convert_split(raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert one split's raw sentence-level data into the processed format.
    Args:
        raw_data: List of sentence dicts, each with 'tokens', 'vertexSet', 'edgeSet'.
    Returns:
        list[dict]: Processed sentence dicts with text, entities, and relations.
    """
    processed: list[dict[str, Any]] = []

    for sent_idx, item in enumerate(raw_data):
        tokens = item["tokens"]
        text = " ".join(tokens)

        entities = extract_entities(item["vertexSet"])
        tokpos_lookup = build_tokpos_to_text(item["vertexSet"])
        relations = extract_relations(item["edgeSet"], tokpos_lookup)

        processed.append(
            {
                "sent_id": sent_idx,
                "text": text,
                "entities": entities,
                "relations": relations,
            }
        )

    return processed

def main():
    """
    Main function to convert PcMSP raw vertex/edge graph data into processed JSON files for train, dev, and test splits.
    """
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Convert PcMSP raw vertex/edge data to processed JSON.")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/gold-standard-datasets/PcMSP/raw"), help="Directory containing raw split files.")
    parser.add_argument("--out-dir", type=Path, default=Path("data/gold-standard-datasets/PcMSP/processed"), help="Output directory for processed JSON files.")

    # Parse arguments
    args = parser.parse_args()

    # Setup and Initialize Module Logging
    logger = LogHandler.setup_module_logging("convert_pcmsp")
    logger.info("Starting PcMSP data conversion script...")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    splits = {
        "mat_train.json": "train.json",
        "mat_dev.json": "validation.json",
        "mat_test.json": "test.json",
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
        total_rels = sum(len(s["relations"]) for s in processed)
        total_ents = sum(
            sum(
                len(v) for v in s["entities"].values()
            )
            for s in processed
        )
        logger.info(f"  -> {out_path}: {len(processed)} sentences, {total_ents} entities, {total_rels} relations")

    logger.info("Done.")

if __name__ == "__main__":
    main()
