import logging
import argparse

from scikg_extract.services.pubchem_cid_mapping import build_lmdb_from_file

if __name__ == "__main__":

    # Add argument parser for PubChem LMDB build
    parser = argparse.ArgumentParser(description="Build PubChem CID-Synonym LMDB database.")
    parser.add_argument("--input_file", type=str, help="Path to the input TSV file.")
    parser.add_argument("--lmdb_path", type=str, help="Path to the output LMDB database.")
    parser.add_argument("--compression", action="store_true", default=True, help="Enable compression for LMDB values.")
    parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose logging.")

    # Parse the arguments
    args = parser.parse_args()

    # Configure the logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Initialize the logger
    logger = logging.getLogger(__name__)
    logger.info(f"Starting PubChem LMDB build...")

    # PubChem data file path
    input_file = args.input_file if args.input_file else "data/resources/Pubchem-CID-Synonym-filtered"
    logger.info(f"PubChem Input file: {input_file}")

    # PubChem LMDB output path
    lmdb_path = args.lmdb_path if args.lmdb_path else "data/external/pubchem/pubchem_cid_lmdb"
    logger.info(f"PubChem LMDB output path: {lmdb_path}")

    # Build the LMDB database from the input TSV file
    logger.info("Building PubChem LMDB database...")
    build_lmdb_from_file(input_file, lmdb_path, compression=args.compression)