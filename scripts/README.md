# 📋 Overview

This directory contains various scripts used throughout the SciKG-Extract project. The scripts are organized by functionality to test different components of the extraction pipeline, including data extraction, text processing, chemical normalization, JSON handling, data export, statistics generation, and evaluation.

# 📁 Directory Structure

```
scripts/
├── data_extraction/                                    # Scripts for extracting structured data from scientific papers using SciKG_Extract workflow
│   └── extract_ald_info.py                             # Extract structured data for ALD processes using SciKG_Extract workflow
├── text_extraction/                                    # Scripts for extracting raw text from documents
│   └── pdf_text_extraction.py                          # Extract text content from PDF documents
├── pubchem/                                            # Scripts related to PubChem
│   ├── pubchem_api.py                                  # PubChem API interface
│   ├── pubchem_lmdb.py                                 # Create local LMDB database for PubChem data
│   ├── pubchem_lookup.py                               # PubChem data lookup tests
│   └── pubchem_normalization.py                        # Normalize chemical names using PubChem data
├── json/                                               # Utitity scripts for JSON management
│   ├── json_cleaner.py                                 # Clean JSON data by removing nulls and empty structures
│   └── json_validator.py                               # Validate JSON schema and JSON data against a schema
├── data_export/                                        # Export data to various formats
│   └── json_to_excel.py                                # Expert JSON data to Excel format
├── statistics/                                         # Generate statistics and reports
│   └── data_statistics.py                              # Generate overview statistics from extracted data
└── evaluation/                                         # Evaluate extraction quality and accuracy
    └── compare_extracted_data_with_atomiclimits.py     # Compare extracted data with AtomicLimits database annotations
```

## 🚀 Usage

The scripts in this directory can be executed individually to perform specific tasks related to the SciKG-Extract project. Below are some general guidelines on how to use these scripts:

1. **Keyword Arguments**: All scripts accept command-line arguments to specify input and output locations, and other configuration options. Use the `--help` flag with any script to see available options.
2. **Logging**: Most scripts include logging functionality to provide feedback during execution. Check the console output or log files for progress and error messages.
3. **Dependencies**: Ensure that all required dependencies are installed in your Python environment. Refer to the requirements.txt file in the root directory of the project for a list of necessary packages.
4. **Modular Execution**: Each script is designed to perform a specific function. You can run them independently based on your needs, such as extracting text from PDFs, normalizing chemical names, or validating JSON data.

**Example Usage**:
```bash
python scripts/json/json_validator.py --schema path/to/schema.json --instance path/to/data.json --verbose
```
