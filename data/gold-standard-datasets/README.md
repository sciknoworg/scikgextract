# Gold-Standard Datasets

Benchmark datasets used for evaluating extraction performance across multiple scientific domains. Each sub-dataset has its own README with detailed statistics and format descriptions.

## Contents

| Dataset | Domain | Documents | Entity Types | Relation Types | Splits |
|---|---|---|---|---|---|
| [BC5CDR](BC5CDR/README.md) | Biomedical | 1,500 PubMed abstracts | 2 (Chemical, Disease) | 1 (CID) | Train / Val / Test (500 each) |
| [BioRED](BioRED/README.md) | Biomedical | 600 PubMed abstracts | 6 | 8 | Train (400) / Val (100) / Test (100) |
| [PcMSP](PcMSP/README.md) | Materials science | 2,379 sentences | 7 | 1 (action graph) | Train (1,957) / Val (273) / Test (149) |
| [PolyIE](PolyIE/readme.md) | Polymer science | 90 papers / 632 sentences | 4 | 2 (3- and 4-element tuples) | Train (63) / Val (13) / Test (14) |

## Structure

Each sub-dataset folder follows the same layout:

```
<dataset>/
├── raw/          # Original source files in the dataset's native format
├── processed/    # Standardised JSON files consumed by extraction scripts
│   ├── train.json
│   ├── validation.json
│   └── test.json
└── README.md     # Dataset-specific statistics and format description
```

The `processed/` JSON files are generated from `raw/` by the conversion scripts in `scripts/data_processing/gold-standard-datasets/` (e.g. `convert_bc5cdr.py`, `convert_biored.py`).
