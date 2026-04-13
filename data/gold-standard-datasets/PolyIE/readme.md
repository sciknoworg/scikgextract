# PolyIE: A Dataset of Information Extraction from Polymer Material Scientific Literature

## Overview

**PolyIE** is a gold-standard dataset for information extraction from polymer material scientific literature. It contains annotated scientific papers with polymer names, measured property names, property values, and experimental conditions, along with relations linking chemicals to their properties and measurements. The dataset was designed to support Named Entity Recognition (NER) and Relation Extraction (RE) tasks in the polymer science domain.

- **Domain:** Polymer science / materials science
- **Source:** Publicly available scientific papers on polymer materials
- **Annotation Level:** Sentence-level (BIO-tagged tokens + relation index spans)
- **Splits:** Train / Validation / Test

## Dataset Statistics

### Summary

| Split | Documents | Sentences | Entities | Relations |
|:------|----------:|----------:|---------:|----------:|
| Train | 63 | 435 | 13,257 | 1,963 |
| Validation | 13 | 100 | 3,187 | 500 |
| Test | 14 | 97 | 3,463 | 528 |
| **Total** | **90** | **632** | **19,907** | **2,991** |

### Entity Type Breakdown

| Entity Type | Train | Validation | Test | Total |
|:------------|------:|-----------:|-----:|------:|
| Chemical Names (CN) | 5,131 | 1,214 | 1,241 | 7,586 |
| Property Names (PN) | 4,487 | 1,117 | 1,276 | 6,880 |
| Property Values (PV) | 3,396 | 813 | 897 | 5,106 |
| Conditions | 243 | 43 | 49 | 335 |

### Relation Type Breakdown

Relations are structured tuples of varying arity:

| Relation Type | Train | Validation | Test | Total |
|:--------------|------:|-----------:|-----:|------:|
| 3-element (CN, PN, PV) | 1,701 | 476 | 500 | 2,677 |
| 4-element (CN, PN, PV, Condition) | 250 | 24 | 27 | 301 |
| 2-element (CN, PN) | 12 | 0 | 1 | 13 |

## Schema

The extraction schema defines 4 entity types and 1 relation structure:

### Entity Types

| Entity Type | Description | Example |
|:------------|:------------|:--------|
| `chemicalNames` | Chemical or polymer names and abbreviations | P3HT, PEDOT:PSS, poly(3-hexylthiophene) |
| `propertyNames` | Names of measured properties | PCE, Voc, Jsc, band gap, decomposition temperature |
| `propertyValues` | Measured values with units | 3.8%, 0.9 V, 437 °C |
| `conditions` | Experimental conditions for measurements | 5% weight loss, room temperature, under N₂ |

### Relation Structure

Each relation links a chemical to a property measurement:

| Field | Required | Description |
|:------|:---------|:------------|
| `chemicalName` | Yes | The chemical/polymer this property belongs to |
| `propertyName` | Yes | The name of the measured property |
| `propertyValue` | No | The measured value with unit |
| `condition` | No | The experimental condition, if applicable |

Full schema: [`data/schemas/PolyIE/PolyIE-schema.json`](../../schemas/PolyIE/PolyIE-schema.json)

## Citation

If you use this dataset, please cite the original PolyIE paper:

```bibtex
@inproceedings{cheung2024polyie,
  title={POLYIE: A dataset of information extraction from polymer material scientific literature},
  author={Cheung, Jerry and Zhuang, Yuchen and Li, Yinghao and Shetty, Pranav and Zhao, Wantian and Grampurohit, Sanjeev and Ramprasad, Rampi and Zhang, Chao},
  booktitle={Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers)},
  pages={2370--2385},
  year={2024}
}
```

## Source

- **Source:** [PolyIE GitHub Repository](https://github.com/jerry3027/PolyIE/tree/main/Cleaned_data/Final_v2)
