"""
Script to lookup PubChem CID by Synonym from LMDB database. The lookup function supports exact match, substring match, and fuzzy match options.

Author: Sameer Sadruddin
Created: 15th December 2025
Modified: 15th December 2025
"""
# Python Imports
import argparse

# SciKG-Extract Utility Imports
from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.utils.string_utils import normalize_string

# SciKG-Extract Service Imports
from scikg_extract.services.pubchem_cid_mapping import open_env_for_read, lookup_by_synonym

if __name__ == "__main__":
    """Script to lookup PubChem CID by Synonym from LMDB database."""

    # Add argument parser for PubChem LMDB lookup
    parser = argparse.ArgumentParser(description="Lookup PubChem CID by Synonym in LMDB database.")
    parser.add_argument("--lmdb_path", type=str, help="Path to the PubChem LMDB database.")
    parser.add_argument("--synonym", type=str, help="Synonym to lookup in PubChem LMDB.")
    parser.add_argument("--compression", action="store_true", default=True, help="Enable compression for LMDB values.")
    
    # Parse the arguments
    args = parser.parse_args()

    # Configure and Initialize the logger
    logger = LogHandler.setup_module_logging("pubchem_lmdb_lookup")
    logger.info(f"Starting PubChem LMDB lookup...")

    # PubChem LMDB path
    lmdb_path = args.lmdb_path if args.lmdb_path else "data/external/pubchem/pubchem_cid_lmdb"
    logger.info(f"PubChem LMDB path: {lmdb_path}")

    # Open the LMDB environment for reading
    env = open_env_for_read(lmdb_path, readonly=True)

    # Synonym to lookup
    synonym = args.synonym if args.synonym else "Al2O3"
    logger.info(f"Looking up synonym: {synonym}")

    # Normalize the synonym
    synonym = normalize_string(synonym)
    logger.info(f"Normalized synonym: {synonym}")

    # Perform the lookup
    result = lookup_by_synonym(env, synonym, compression=args.compression, enable_substring_match=False, enable_fuzzy=False)
    logger.info(f"Lookup result for '{synonym}': {result}")

    # Close the LMDB environment
    env.close()