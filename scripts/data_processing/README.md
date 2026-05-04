# Data Processing Scripts

Scripts for converting gold-standard NLP benchmark datasets into the unified JSON format used by SciKGExtract.

## Directory Structure

```
data_processing/
└── gold-standard-datasets/
    ├── convert_bc5cdr.py
    ├── convert_biored.py
    ├── convert_pcmsp.py
    └── convert_polyie.py
```

## Scripts

### `convert_bc5cdr.py`

Converts the BC5CDR corpus from **PubTator format** (`.pubtator`) into a unified JSON file.

- **Input format**: PubTator — one document per block with `|t|` (title), `|a|` (abstract), entity annotation lines, and relation lines.
- **Output**: `data/gold-standard-datasets/BC5CDR/<split>.json`

```bash
python 'scripts/data_processing/gold-standard-datasets/convert_bc5cdr.py'
```

### `convert_biored.py`

Converts the BioRED corpus from **BioC JSON format** into a unified JSON file.

- **Input format**: BioC JSON — a single JSON file containing a list of documents with passages, annotations, and relations.
- **Output**: `data/gold-standard-datasets/BioRED/<split>.json`

```bash
python 'scripts/data_processing/gold-standard-datasets/convert_biored.py'
```

### `convert_pcmsp.py`

Converts the PcMSP corpus from a **vertex/edge graph format** into a unified JSON file.

- **Input format**: Graph structure with vertices (entities) and edges (relations).
- **Output**: `data/gold-standard-datasets/PcMSP/<split>.json`

```bash
python 'scripts/data_processing/gold-standard-datasets/convert_pcmsp.py'
```

### `convert_polyie.py`

Converts the PolyIE corpus from **BIO-tagged token format** into a unified JSON file.

- **Input format**: Tab-separated token files with BIO entity tags.
- **Output**: `data/gold-standard-datasets/PolyIE/<split>.json`

```bash
python 'scripts/data_processing/gold-standard-datasets/convert_polyie.py'
```

## Output Format

All scripts produce a list of documents in the following unified structure:

```json
[
  {
    "doc_id": "12345678",
    "title": "...",
    "abstract": "...",
    "entities": [
      {"text": "...", "type": "Chemical", "start": 10, "end": 20}
    ],
    "relations": [
      {"type": "CID", "arg1": "...", "arg2": "..."}
    ]
  }
]
```

## Prerequisites

Download each dataset and place the raw files in `data/gold-standard-datasets/<Dataset>/raw/` before running the conversion scripts. See `data/gold-standard-datasets/` for the expected directory structure per dataset.
