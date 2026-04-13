# BC5CDR — BioCreative V CDR task corpus: a resource for chemical disease relation extraction

## Overview

**BC5CDR** (BioCreative V Chemical-Disease Relation) is a gold-standard dataset for chemical and disease entity recognition and chemical-induced-disease (CID) relation extraction from PubMed abstracts. It was created for the BioCreative V shared task and contains 1,500 PubMed articles with manually annotated chemical and disease mentions linked to MeSH identifiers, along with document-level CID relations.

- **Domain:** Biomedical
- **Source:** PubMed abstracts (1,500 articles)
- **Annotation Level:** Document-level (entity mentions with MeSH IDs + document-level CID relations)
- **Splits:** Train / Validation / Test (500 documents each)

## Dataset Statistics

### Summary

| Split | Documents | Entities | Chemical Mentions | Disease Mentions | CID Relations |
|:------|----------:|---------:|------------------:|-----------------:|--------------:|
| Train | 500 | 9,385 | 5,203 | 4,182 | 1,038 |
| Validation | 500 | 9,591 | 5,347 | 4,244 | 1,012 |
| Test | 500 | 9,809 | 5,385 | 4,424 | 1,066 |
| **Total** | **1,500** | **28,785** | **15,935** | **12,850** | **3,116** |

### Entity Type Breakdown

| Metric | Train | Validation | Test | Total |
|:-------|------:|-----------:|-----:|------:|
| Chemical mentions | 5,203 | 5,347 | 5,385 | 15,935 |
| Disease mentions | 4,182 | 4,244 | 4,424 | 12,850 |
| Unique Chemical MeSH IDs | 665 | 661 | 675 | — |
| Unique Disease MeSH IDs | 696 | 634 | 673 | — |

### Relation Statistics

All relations in BC5CDR are of a single type: **CID** (Chemical-Induced-Disease). Each relation is a document-level assertion linking a chemical MeSH ID to a disease MeSH ID.

| Split | CID Relations | Avg. Relations per Document |
|:------|:-------------|:---------------------------|
| Train | 1,038 | 2.08 |
| Validation | 1,012 | 2.02 |
| Test | 1,066 | 2.13 |

## Schema

The extraction schema defines 2 entity types and 1 relation type:

### Entity Types

| Entity Type | Description | Identifier | Example |
|:------------|:------------|:-----------|:--------|
| `Chemical` | Chemical compounds, drugs, and substances | MeSH ID (e.g., D009270) | Naloxone, clonidine, lidocaine |
| `Disease` | Diseases, symptoms, and adverse effects | MeSH ID (e.g., D006973) | hypertensive, cardiac asystole, depression |

> Entities with no MeSH mapping have `identifier` set to `"-1"`. This occurs for composite mentions, abbreviations, or mentions that cannot be normalized to a single MeSH concept.

### Relation Types

| Relation Type | Description |
|:--------------|:------------|
| `CID` | Chemical-Induced-Disease: the chemical causes or induces the disease/adverse effect |

Each CID relation links a chemical MeSH ID to a disease MeSH ID at the document level.

Full schema: [`data/schemas/BC5CDR/BC5CDR-schema.json`](../../schemas/BC5CDR/BC5CDR-schema.json)

## Citation

If you use this dataset, please cite the original BC5CDR papers:

```bibtex
@article{li2016biocreative,
  title={BioCreative V CDR task corpus: a resource for chemical disease relation extraction},
  author={Li, Jiao and Sun, Yueping and Johnson, Robin J and Sciaky, Daniela and Wei, Chih-Hsuan and Leaman, Robert and Davis, Allan Peter and Mattingly, Carolyn J and Wiegers, Thomas C and Lu, Zhiyong},
  journal={Database},
  volume={2016},
  year={2016},
  publisher={Oxford Academic}
}
```

## Source

- **Source:** [BioCreative V CDR Task](https://github.com/JHnlp/BioCreative-V-CDR-Corpus)