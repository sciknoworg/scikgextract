# Python imports
import zlib
import logging
from typing import List, Tuple

# External imports
import lmdb
from rapidfuzz import fuzz

def build_lmdb_from_file(input_file: str, lmdb_path: str, map_size: int = 15 * 1024**3, compression: bool = True) -> None:
    """
    Build an LMDB database from a tab-separated values (TSV) file with CID and synonym columns.

    Args:
        input_file (str): Path to the input TSV file.
        lmdb_path (str): Path to the output LMDB database.
        compression (bool): Whether to use compression for the values.
        map_size (int): Maximum size of the LMDB database in bytes.
    """

    # Initialize logging
    logger = logging.getLogger(__name__)
    logger.info(f"Building LMDB database at {lmdb_path} from file {input_file}")

    # Total processed counter and log interval
    total_processed = 0
    log_interval = 100000

    # Create or open the LMDB environment
    env = lmdb.open(lmdb_path, map_size=map_size, subdir=False, readonly=False, metasync=False, sync=False, readahead=True, writemap=False)

    # Start a write transaction
    logging.info("Starting to read input file and populate LMDB...")
    with env.begin(write=True) as txn:
        
        # Read the input file line by line
        with open(input_file, 'r', encoding='utf-8') as f:
            
            # Iterate through each line in the file
            for line in f:
                
                # Remove leading/trailing whitespace and skip empty lines
                line = line.strip()
                if not line: continue

                # Split by tab, expecting two columns: CID and synonym
                cid, synonym = line.split('\t')

                # Encode key and value with utf-8
                key = synonym.encode('utf-8')
                value = cid.encode('utf-8')

                # Compress the value if needed
                if compression:
                    key = zlib.compress(key)
                
                # Store the key-value pair in the LMDB and update counter
                txn.put(key, value)
                total_processed += 1

                # Log total processed entries
                if total_processed % log_interval == 0:
                    logger.info(f"Processed {total_processed} records...")
    
    # Close the LMDB environment
    logger.info(f"Finished building LMDB database with total {total_processed} records.")
    env.close()

def open_env_for_read(lmdb_path: str, readonly: bool = True) -> lmdb.Environment:
    """
    Open an LMDB environment for reading.
    Args:
        lmdb_path (str): Path to the LMDB database.
        readonly (bool): Whether to open the database in read-only mode.
    Returns:
        lmdb.Environment: The opened LMDB environment.
    """
    # Open an LMDB environment for reading
    env = lmdb.open(lmdb_path, subdir=False, readonly=readonly, readahead=True)

    # Return the LMDB environment
    return env

def lookup_by_synonym(env: lmdb.Environment, synonym: str, compression: bool = True, enable_fuzzy: bool = True, enable_substring_match: bool = True, match_threshold: int = 85) -> List[Tuple[str, str]]:
    """
    Lookup CIDs by synonym in the LMDB database with exact, substring, and fuzzy matching.
    Args:
        env (lmdb.Environment): The LMDB environment.
        synonym (str): The synonym to look up.
        compression (bool): Whether the values are compressed.
        enable_fuzzy (bool): Whether to enable fuzzy matching.
        enable_substring_match (bool): Whether to enable substring matching.
        match_threshold (int): The threshold score for fuzzy matching (0-100).
    Returns:
        List[Tuple[str, str]]: A list of matching CIDs with its synonym or empty list if not found.
    """

    # Initialize the logger
    logger = logging.getLogger(__name__)
    logger.info(f"Looking up synonym: {synonym} (Fuzzy: {enable_fuzzy}, Substring: {enable_substring_match})")

    # Initialize list to hold matching CIDs
    matching_cids: List[Tuple[str, str]] = []

    # Start a read transaction
    with env.begin(write=False) as txn:
        # Encode and possibly compress the synonym key
        syn_key = synonym.encode('utf-8')
        syn_key_c = zlib.compress(syn_key) if compression else syn_key

        # Try exact match first
        raw = txn.get(syn_key_c)
        if raw:
            logger.info(f"Exact match found for synonym: {synonym} with CID: {raw.decode('utf-8')}")
            matching_cids.append((synonym, raw.decode('utf-8')))
            return matching_cids

        # If not found, use substring to find the closest matches among all keys
        if enable_substring_match:
            logger.info(f"Attempting substring match for synonym: {synonym}")
            
            with txn.cursor() as cursor:
                for key, value in cursor:
                    
                    # Decompress key if needed
                    key_dec = zlib.decompress(key) if compression else key

                    # Decode key
                    key_str = key_dec.decode('utf-8')

                    # Substring match check
                    if synonym.lower() in key_str.lower() or key_str.lower() in synonym.lower():
                        matching_cids.append((key_str, value.decode('utf-8')))
    
        # Filter list further with fuzzy matching and remove candidates below threshold
        if enable_fuzzy:
            logger.info(f"Attempting fuzzy match for synonym: {synonym} in the list of matching candidates having {len(matching_cids)} entries")

            # Iterate over the matching CIDs and calculate fuzzy scores
            for key_str, cid in matching_cids.copy():

                # Calculate fuzzy match score
                score = fuzz.ratio(synonym, key_str)

                # Check if the score meets the threshold
                if score < match_threshold:
                    matching_cids.remove((key_str, cid))
        
    # Return the list of matching CIDs
    return matching_cids