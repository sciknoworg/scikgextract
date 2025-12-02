import argparse

from scikg_extract.utils.log_handler import LogHandler
from scikg_extract.services.pubchem_cid_mapping import build_lmdb_from_file

if __name__ == "__main__":

    # Add argument parser for PubChem LMDB build
    parser = argparse.ArgumentParser(description="Build PubChem CID-Synonym LMDB database.")
    parser.add_argument("--input_file", type=str, help="Path to the input TSV file.")
    parser.add_argument("--lmdb_path", type=str, help="Path to the output LMDB database.")
    parser.add_argument("--compression", action="store_true", default=True, help="Enable compression for LMDB values.")

    # Parse the arguments
    args = parser.parse_args()

    # Configure and Initialize Logger
    logger = LogHandler.setup_module_logging("pubchem_lmdb_build")
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