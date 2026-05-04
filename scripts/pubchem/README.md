# PubChem Scripts

Scripts for building a local PubChem lookup database (LMDB) and normalizing extracted chemical compound names to PubChem Compound IDs (CIDs).

## Scripts

| Script | Purpose |
|---|---|
| `pubchem_api.py` | Fetch compound properties and synonyms from the PubChem REST API |
| `pubchem_lmdb.py` | Build a local LMDB key-value store from the PubChem CID-Synonym TSV file |
| `pubchem_lookup.py` | Look up PubChem CIDs for a given chemical name using the LMDB database |
| `pubchem_normalization.py` | Normalize compound names in extracted JSON files by adding `sameAs` CID URIs |

## Recommended Execution Order

1. Download the PubChem CID-Synonym TSV file (see below)
2. Build the LMDB database with `pubchem_lmdb.py`
3. Normalize extractions with `pubchem_normalization.py` (or run `pubchem_lookup.py` for ad-hoc lookups)

---

## Step 1 — Download PubChem Data

Download the CID-Synonym file from the PubChem FTP server:

```
ftp://ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras/CID-Synonym-filtered.gz
```

Decompress and place the file at:

```
data/resources/Pubchem-CID-Synonym-filtered
```

---

## Step 2 — Build the LMDB Database

```bash
python scripts/pubchem/pubchem_lmdb.py \
    --input_file "data/resources/Pubchem-CID-Synonym-filtered" \
    --lmdb_path "data/external/pubchem/pubchem_cid_lmdb"
```

**Arguments:**

| Argument | Default | Description |
|---|---|---|
| `--input_file` | `data/resources/Pubchem-CID-Synonym-filtered` | Path to the PubChem TSV synonym file |
| `--lmdb_path` | `data/external/pubchem/pubchem_cid_lmdb` | Output path for the LMDB database directory |
| `--compression` | `True` | Compress stored values with zlib |

---

## Step 3a — Normalize Extractions

Adds `sameAs` PubChem CID URIs to every compound field in a directory of extraction JSON files:

```bash
python scripts/pubchem/pubchem_normalization.py \
    --input_dir "results/extractions/ALD/experiment3/gpt-4o" \
    --lmdb_path "data/external/pubchem/pubchem_cid_lmdb"
```

Writes updated JSON files in-place (or to a separate output directory if configured).

---

## Step 3b — Ad-hoc Lookup

Look up the PubChem CID for a single compound name:

```bash
python scripts/pubchem/pubchem_lookup.py \
    --name "trimethylaluminum" \
    --lmdb_path "data/external/pubchem/pubchem_cid_lmdb"
```

Or use the REST API fallback (no LMDB required):

```bash
python scripts/pubchem/pubchem_api.py --name "trimethylaluminum"
```

---

## Lookup Strategy

The `pubchem_normalization.py` script tries multiple strategies in order:

1. **Exact match** — direct string lookup in LMDB
2. **Normalized match** — lowercase + stripped string lookup
3. **PubChem REST API** — fallback for names not found locally

Matched CIDs are appended to the `sameAs` field of each compound entity as URIs in the form `https://pubchem.ncbi.nlm.nih.gov/compound/<CID>`.
