# Normalization Scripts

Post-processing scripts for correcting and augmenting normalization data in extracted knowledge files.

## Scripts

### `normalization_correction.py`

Applies corrections to already-extracted JSON files by adding PubChem CIDs to compound entries that were missed or incorrectly normalized during the original extraction run.

This script reads extraction results from disk, looks up PubChem CIDs for compound property values, and writes the updated JSON files back with the `sameAs` field populated.

#### Usage

```bash
python scripts/normalization/normalization_correction.py
```

The script uses default paths configured at the top of the file. Key paths:

| Variable | Default | Description |
|---|---|---|
| Input directory | `results/extractions/ALD/...` | Directory of JSON extraction files to correct |
| LMDB path | `data/external/pubchem/pubchem_cid_lmdb` | Local PubChem LMDB database |
| Property path | Schema-dependent | JSON path to the compound fields to normalize |

#### Prerequisites

- The LMDB database must be built first. See [`scripts/pubchem/README.md`](../pubchem/README.md).
- Run after the main extraction pipeline when normalization was skipped or incomplete.

#### What it does

1. Iterates over all JSON extraction files in the input directory
2. For each compound property entry, looks up PubChem CIDs using the LMDB database (exact match, then normalized string match, then REST API fallback)
3. Appends discovered CID URIs to the `sameAs` list of each entry
4. Saves the corrected JSON file back to disk
