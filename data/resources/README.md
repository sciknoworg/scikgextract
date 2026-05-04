# Resources

Static lookup files used for chemical entity normalization. These files map chemical synonyms to PubChem CIDs and are consumed by the normalization step of the extraction pipeline.

## Contents

| File | Description |
|---|---|
| `Pubchem-CID-Synonym-filtered` | Raw TSV source file downloaded from the PubChem FTP site. Input to the LMDB build script. **Not tracked in version control** (gitignored due to size). |
| `PubChem-Synonym-CID.json` | JSON dictionary mapping chemical synonyms to PubChem CIDs. Built from the raw TSV and used at runtime for fast in-memory lookups. |

## How to Generate

**Step 1 — Download the raw TSV** from the [PubChem FTP site](https://ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras/CID-Synonym-filtered.gz), decompress it, and place it at `data/resources/Pubchem-CID-Synonym-filtered`.

**Step 2 — Build the LMDB database** (used by normalization-enabled extraction scripts):

```bash
python scripts/pubchem/pubchem_lmdb.py
```

This writes the LMDB database to `data/external/pubchem/pubchem_cid_lmdb`.
