# Research Papers

Source scientific literature used as input to the extraction pipeline. Papers are stored in both PDF (original) and Markdown (converted) formats. The Markdown versions are what extraction scripts consume at runtime via `--scientific_docs_dir`.

## Structure

```
research-papers/
├── ALD/                        # Atomic Layer Deposition papers
│   ├── pdf/
│   │   ├── AtomicLimits Database/  # 650+ material folders from the AtomicLimits DB
│   │   ├── ZnO-IGZO-papers/        # Experimental use-case subset (ZnO & IGZO)
│   │   └── Others/                 # Additional ALD-related papers
│   └── markdown/               # Markdown conversions (mirrors pdf/ structure)
│       ├── AtomicLimits Database/
│       ├── ZnO-IGZO-papers/
│       └── Others/
└── ALE/                        # Atomic Layer Etching papers
    ├── pdf/
    │   ├── experimental-usecase/
    │   └── simulation-usecase/
    └── markdown/               # Markdown conversions (mirrors pdf/ structure)
        ├── experimental-usecase/
        └── simulation-usecase/
```

## PDF → Markdown Conversion

Markdown files are generated from PDFs using:

```bash
python scripts/text_extraction/pdf_text_extraction.py
```

Run this script whenever new PDFs are added before using them in an extraction pipeline.

## Closed-Source Papers (ZnO & IGZO)

The papers under `ALD/pdf/ZnO-IGZO-papers/experimental-usecase/` and `ALD/pdf/AtomicLimits Database/` are sourced from the [AtomicLimits Database](https://www.atomiclimits.com/) and are not redistributed in this repository due to their closed-source nature. Each material folder contains a `paper_details.csv` with the paper title, authors, and DOI link for independent access.

> [!NOTE]
> Sub-folders under `ALD/` and `ALE/` are named after the material, precursor, and co-reactant combination (e.g. `ZnEt2 - H2O`), matching the folder structure used in `gold-standard-annotations/`.
