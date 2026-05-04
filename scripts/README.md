# Overview

This directory contains scripts used throughout the SciKG-Extract project, organized by functionality: knowledge extraction, evaluation, data processing, chemical normalization, JSON utilities, data export, statistics, and ORKG integration.

# Directory Structure

```
scripts/
├── knowledge_extraction/               # LLM-based knowledge extraction experiments (6 domains × up to 6 pipelines)
│   ├── ZnO-IGZO-Papers/                #   ALD ZnO & IGZO papers — 6 experiment variants
│   ├── AtomicLimits Database/          #   ALD ZnO & IGZO — AtomicLimits sub-corpus (4 variants)
│   ├── BC5CDR/                         #   Chemical-disease relation extraction (4 variants)
│   ├── BioRED/                         #   Biomedical entity & relation extraction (4 variants)
│   ├── PcMSP/                          #   Materials synthesis procedure extraction (4 variants)
│   └── PolyIE/                         #   Polymer property extraction (4 variants)
├── evaluation/                         # Evaluate extraction results against gold-standard or LLM-as-a-Judge
│   ├── evaluate_bc5cdr.py              #   BC5CDR entity + relation P/R/F1
│   ├── evaluate_biored.py              #   BioRED entity + relation P/R/F1
│   ├── evaluate_pcmsp.py               #   PcMSP entity + relation P/R/F1
│   ├── evaluate_polyie.py              #   PolyIE entity + relation P/R/F1
│   ├── evaluate_zno_igzo.py            #   ZnO/IGZO per-field P/R/F1 vs. AtomicLimits annotations
│   ├── llm_as_a_judge_evaluation.py    #   LLM-as-a-Judge (Correctness + Completeness rubrics)
│   └── compare_extracted_data_with_atomiclimits.py  # Compare extractions against AtomicLimits DB
├── data_processing/                    # Convert gold-standard datasets to unified JSON format
│   └── gold-standard-datasets/
│       ├── convert_bc5cdr.py           #   PubTator → JSON
│       ├── convert_biored.py           #   BioC JSON → JSON
│       ├── convert_pcmsp.py            #   Vertex/edge graph → JSON
│       └── convert_polyie.py           #   BIO-tagged tokens → JSON
├── pubchem/                            # PubChem CID lookup and normalization
│   ├── pubchem_api.py                  #   PubChem REST API client
│   ├── pubchem_lmdb.py                 #   Build local LMDB from CID-Synonym TSV
│   ├── pubchem_lookup.py               #   Ad-hoc CID lookup against LMDB
│   └── pubchem_normalization.py        #   Normalize compound names in extraction JSON files
├── normalization/                      # Post-hoc normalization corrections
│   └── normalization_correction.py     #   Add missing PubChem CIDs to existing extractions
├── orkg/                               # Export structured knowledge to ORKG
│   └── export_to_orkg.py               #   Materialize ALD/ALE records as ORKG resources + statements
├── json/                               # JSON utility scripts
│   ├── json_cleaner.py                 #   Remove nulls and empty QUDT structures
│   └── json_validator.py               #   Validate JSON schema and instances (Draft7)
├── data_export/                        # Export extracted data to other formats
│   ├── export_atomiclimits_fields.py   #   Export selected fields from AtomicLimits extractions
│   └── json_to_excel.py                #   Convert extraction JSON files to Excel spreadsheets
├── statistics/                         # Summarize extraction coverage and dataset statistics
│   └── data_statistics.py              #   Generate overview statistics from extracted data
└── text_extraction/                    # Extract raw text from source documents
    └── pdf_text_extraction.py          #   PDF → Markdown text extraction
```

## Usage

All scripts accept command-line arguments. Use `--help` with any script to see available options:

```bash
python scripts/<subfolder>/<script>.py --help
```

Detailed usage instructions and argument references are available in the `README.md` of each subfolder:

- [knowledge_extraction/README.md](knowledge_extraction/README.md)
- [evaluation/README.md](evaluation/README.md)
- [data_processing/README.md](data_processing/README.md)
- [pubchem/README.md](pubchem/README.md)
- [normalization/README.md](normalization/README.md)

## General Notes

- **Logging**: All scripts use `LogHandler` from `scikg_extract.utils.log_handler`. Logs are written under `logs/scikg_extract/`.
- **LLM format**: Scripts that invoke LLMs accept the `PROVIDER:model_name` format (e.g., `OPENAI:gpt-4o`, `SAIA:deepseek/deepseek-r1-0528`).

**Example**:
```bash
python scripts/json/json_validator.py --schema path/to/schema.json --instance path/to/data.json --verbose
```
