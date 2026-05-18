"""
Build a CID-to-representations dictionary by fetching IUPACName, MolecularFormula,
and synonyms from the PubChem API for every distinct CID found across the normalized
extraction results. Saves the result to data/resources/pubchem_cid_representations.json.

Usage:
    python scripts/pubchem/build_cid_representations.py
    python scripts/pubchem/build_cid_representations.py --extractions_dir results/extractions/ZnO-IGZO-Papers
    python scripts/pubchem/build_cid_representations.py --output data/resources/pubchem_cid_representations.json
    python scripts/pubchem/build_cid_representations.py --delay 0.5 --timeout 15

Author: Sameer Sadruddin
"""
# Python Imports
import argparse
import asyncio
import json
import os
import re
import time

# SciKG-Extract Script Imports
from scripts.pubchem.pubchem_api import fetch_compound_by_cid, fetch_synonyms_by_cid

# SciKG-Extract Utility Imports
from scikg_extract.utils.file_utils import read_json_file, save_json_file
from scikg_extract.utils.log_handler import LogHandler

# PubChem API constants
PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
PROPERTIES = ["IUPACName", "MolecularFormula"]
CID_URL_PATTERN = re.compile(r"pubchem\.ncbi\.nlm\.nih\.gov/compound/(\d+)")


def collect_cids_from_extractions(extractions_dir: str) -> set[str]:
    """
    Walk extractions_dir recursively and collect every distinct PubChem CID
    found in sameAs URL strings inside JSON extraction files.

    Args:
        extractions_dir: Root directory containing JSON extraction result files.

    Returns:
        Set of CID strings (numeric, e.g. "14806").
    """
    logger = LogHandler.get_logger("build_cid_representations")
    cids: set[str] = set()
    for root, _dirs, files in os.walk(extractions_dir):
        for fname in files:
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(root, fname)
            try:
                data = read_json_file(fpath)
                text = json.dumps(data)
                found = CID_URL_PATTERN.findall(text)
                cids.update(found)
            except Exception as e:
                logger.warning(f"Could not read {fpath}: {e}")
    logger.info(f"Collected {len(cids)} distinct CIDs from {extractions_dir}")
    return cids


async def fetch_representations_for_cid(
    cid: str,
    delay: float,
    timeout: int,
    logger,
) -> dict:
    """
    Fetch IUPACName, MolecularFormula and synonyms for a single CID.
    Returns a dict with keys: iupac_name, molecular_formula, synonyms.
    On any API failure the affected field is left as None / empty list.

    Args:
        cid: PubChem CID string.
        delay: Seconds to sleep after each API call to respect rate limits.
        timeout: HTTP timeout in seconds.
        logger: Logger instance.

    Returns:
        Dict with chemical representations for the CID.
    """
    entry: dict = {
        "iupac_name": None,
        "molecular_formula": None,
        "synonyms": [],
    }

    # Fetch properties (IUPACName, MolecularFormula)
    try:
        prop_response = await fetch_compound_by_cid(cid, PROPERTIES, PUBCHEM_BASE_URL, timeout)
        if prop_response and prop_response.PropertyTable.Properties:
            item = prop_response.PropertyTable.Properties[0]
            entry["iupac_name"] = item.IUPACName
            entry["molecular_formula"] = item.MolecularFormula
        await asyncio.sleep(delay)
    except Exception as e:
        logger.warning(f"CID {cid}: property fetch failed — {e}")

    # Fetch synonyms
    try:
        syn_response = await fetch_synonyms_by_cid(cid, PUBCHEM_BASE_URL, timeout)
        if syn_response and syn_response.InformationList.Information:
            entry["synonyms"] = syn_response.InformationList.Information[0].Synonym
        await asyncio.sleep(delay)
    except Exception as e:
        logger.warning(f"CID {cid}: synonyms fetch failed — {e}")

    return entry


async def build_representations(
    cids: set[str],
    output_path: str,
    delay: float,
    timeout: int,
    logger,
) -> None:
    """
    Fetch representations for all CIDs and save the result JSON file.
    Skips CIDs already present in the output file (resume support).

    Args:
        cids: Set of CID strings to process.
        output_path: Path to write the output JSON dictionary.
        delay: Seconds to sleep between API calls.
        timeout: HTTP timeout in seconds.
        logger: Logger instance.
    """
    # Load existing results to support resuming an interrupted run
    existing: dict = {}
    if os.path.exists(output_path):
        try:
            existing = read_json_file(output_path)
            logger.info(f"Resuming — {len(existing)} CIDs already in {output_path}")
        except Exception:
            pass

    remaining = sorted(cids - set(existing.keys()))
    logger.info(f"{len(remaining)} CIDs to fetch (skipping {len(existing)} already done)")

    results: dict = dict(existing)
    for i, cid in enumerate(remaining, start=1):
        logger.info(f"[{i}/{len(remaining)}] Fetching CID {cid} ...")
        entry = await fetch_representations_for_cid(cid, delay, timeout, logger)
        results[cid] = entry

        # Checkpoint every 25 CIDs so a crash doesn't lose all progress
        if i % 25 == 0:
            _write_output(results, output_path, logger)

    _write_output(results, output_path, logger)
    logger.info(f"Done. {len(results)} CIDs saved to {output_path}")


def _write_output(results: dict, output_path: str, logger) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Checkpoint saved: {len(results)} entries → {output_path}")


async def main(args) -> None:
    logger = LogHandler.setup_module_logging("build_cid_representations")
    logger.info("Starting CID representations builder...")

    cids = collect_cids_from_extractions(args.extractions_dir)
    if not cids:
        logger.warning("No CIDs found. Check --extractions_dir path.")
        return

    await build_representations(cids, args.output, args.delay, args.timeout, logger)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a CID → chemical representations dictionary from PubChem.")
    parser.add_argument(
        "--extractions_dir",
        default=os.path.join("results", "extractions", "ZnO-IGZO-Papers"),
        help="Root directory of normalized JSON extraction results to scan for CIDs.",
    )
    parser.add_argument(
        "--output",
        default=os.path.join("data", "resources", "pubchem_cid_representations.json"),
        help="Output path for the CID representations JSON file.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Seconds to sleep between PubChem API calls to avoid rate-limiting (default: 0.3).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP timeout in seconds for each API call (default: 10).",
    )
    args = parser.parse_args()
    asyncio.run(main(args))
