# 📋 Overview

This directory contains various resources used in the SciKG-Extract project, including example extractions, gold-standard annotations, research papers, and JSON schema representations.

## 📁 Directory Structure

```
data/
├── examples/                   # Few-shot examples injected into LLM prompts at inference time
├── external/                   # Third-party knowledge bases (PubChem LMDB) for entity normalization
├── gold-standard-annotations/  # Domain-expert annotated data (ALD experimental use-case)
├── gold-standard-datasets/     # Public benchmark datasets (BC5CDR, BioRED, PcMSP, PolyIE)
├── models/                     # Pydantic models for API responses, evaluation, and extraction outputs
│   ├── api/                    # PubChem API response models
│   ├── evaluation/             # LLM judge response models
│   ├── normalization/          # Entity disambiguation models
│   └── schema/                 # Domain-specific extraction output schemas
├── research-papers/            # Source papers in PDF and Markdown formats (ALD, ALE)
├── resources/                  # Lookup tables for chemical entity normalization (PubChem)
└── schemas/                    # JSON Schema files passed to the LLM to constrain extraction output
```

> [!NOTE]
> Several large files are gitignored and **not included in the repository**: `resources/Pubchem-CID-Synonym-filtered`, `external/pubchem/pubchem_cid_lmdb`, and all research paper PDFs and Markdown files under `research-papers/`. Run the setup steps below before using any pipeline that depends on them.

## 🚀 Usage

Each subfolder contains a `README.md` with its purpose, contents, and usage instructions. See the [Data Flow](#-data-flow) section below for how the folders connect at runtime.

## � Before You Start

Three one-time setup steps are required before running any extraction or normalization pipeline:

**1. Convert research papers from PDF to Markdown** (required by all extraction scripts):
```bash
python scripts/text_extraction/pdf_text_extraction.py
```

**2. Build the PubChem LMDB database** (required by normalization-enabled pipelines):
```bash
# First download and decompress to data/resources/Pubchem-CID-Synonym-filtered:
# https://ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras/CID-Synonym-filtered.gz
python scripts/pubchem/pubchem_lmdb.py
```

## 📌 `models/schema/` vs `schemas/`

These two folders are complementary but serve different roles:

| Folder | Format | Purpose |
|---|---|---|
| `schemas/` | JSON Schema (`.json`) | Passed to the LLM via `--process_schema` to constrain output structure |
| `models/schema/` | Pydantic (`.py`) | Used in Python code for response validation and downstream processing |

When adding a new domain, both a JSON Schema file and a matching Pydantic model are needed.

## �📄 ZnO and IGZO ALD Processes - Scientific Papers

See [research-papers/README.md](research-papers/README.md) for the full structure, closed-source access instructions, and PDF → Markdown conversion guide.

## 🔄 Data Flow

The diagram below shows how the resources in this directory feed into the extraction and evaluation pipeline at runtime.

```
research-papers/          → input documents fed to the LLM for extraction  (--scientific_docs_dir)
schemas/                  → constrain LLM output structure  (--process_schema)
examples/                 → few-shot prompt context         (--process_examples)
resources/ + external/    → chemical entity normalization   (--pubchem_lookup_dict_path)
                                                             (--lmdb_pubchem_path)
        ↓
   Extraction output
        ↓
gold-standard-datasets/   → token-level evaluation (BC5CDR, BioRED, PcMSP, PolyIE)
gold-standard-annotations/→ field-level evaluation (ALD ZnO / IGZO)
```