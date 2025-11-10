import logging
import argparse

from scikg_extract.services.pubchem_cid_mapping import open_env_for_read, lookup_by_synonym

if __name__ == "__main__":

    # Add argument parser for PubChem LMDB lookup
    parser = argparse.ArgumentParser(description="Lookup PubChem CID by Synonym in LMDB database.")
    parser.add_argument("--lmdb_path", type=str, help="Path to the PubChem LMDB database.")
    parser.add_argument("--synonym", type=str, help="Synonym to lookup in PubChem LMDB.")
    parser.add_argument("--compression", action="store_true", default=True, help="Enable compression for LMDB values.")
    parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose logging.")
    
    # Parse the arguments
    args = parser.parse_args()

    # Configure the logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Initialize the logger
    logger = logging.getLogger(__name__)
    logger.info(f"Starting PubChem LMDB lookup...")

    # PubChem LMDB path
    lmdb_path = args.lmdb_path if args.lmdb_path else "data/external/pubchem/pubchem_cid_lmdb"
    logger.info(f"PubChem LMDB path: {lmdb_path}")

    # Open the LMDB environment for reading
    env = open_env_for_read(lmdb_path, readonly=True)

    # Synonym to lookup
    synonym = args.synonym if args.synonym else "Zinc"
    logger.info(f"Looking up synonym: {synonym}")

    # Perform the lookup
    result = lookup_by_synonym(env, synonym, compression=args.compression, enable_substring_match=True)
    logger.info(f"Lookup result for '{synonym}': {result}")

    # Close the LMDB environment
    env.close()