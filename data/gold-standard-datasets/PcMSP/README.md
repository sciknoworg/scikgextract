# PcMSP — A Dataset for Scientific Action Graphs Extraction from Polycrystalline Materials Synthesis Procedure Text

## Overview

**PcMSP** is a gold-standard dataset for extracting structured synthesis procedures from materials science literature. It contains annotated sentences from polycrystalline materials synthesis papers, with entity annotations for materials, operations, descriptors, values, properties, devices, and brands, along with typed directed relations capturing the procedural workflow and entity associations.

- **Domain:** Materials science
- **Source:** Scientific literature on polycrystalline materials synthesis
- **Annotation Level:** Sentence-level (vertex/edge graph structure)
- **Splits:** Train / Validation / Test

## Dataset Statistics

### Summary

| Split | Sentences | Entities | Relations |
|:------|----------:|---------:|----------:|
| Train | 1,957 | 11,140 | 11,095 |
| Validation | 273 | 1,471 | 1,373 |
| Test | 149 | 1,420 | 1,372 |
| **Total** | **2,379** | **14,031** | **13,840** |

### Entity Type Breakdown

| Entity Type | Train | Validation | Test | Total |
|:------------|------:|-----------:|-----:|------:|
| Materials | 2,592 | 320 | 344 | 3,256 |
| Operations | 2,413 | 318 | 301 | 3,032 |
| Descriptors | 2,378 | 285 | 301 | 2,964 |
| Values | 1,214 | 172 | 165 | 1,551 |
| Properties | 1,672 | 278 | 204 | 2,154 |
| Devices | 642 | 72 | 87 | 801 |
| Brands | 229 | 26 | 18 | 273 |

#### Material Subtypes

| Subtype | Train | Validation | Test | Total |
|:--------|------:|-----------:|-----:|------:|
| Material-target | 440 | 50 | 56 | 546 |
| Material-recipe | 1,233 | 134 | 155 | 1,522 |
| Material-intermedium | 761 | 123 | 112 | 996 |
| Material-others | 158 | 13 | 21 | 192 |

#### Property Subtypes

| Subtype | Train | Validation | Test | Total |
|:--------|------:|-----------:|-----:|------:|
| Property-temperature | 659 | 112 | 78 | 849 |
| Property-time | 491 | 77 | 67 | 635 |
| Property-pressure | 400 | 66 | 42 | 508 |
| Property-rate | 122 | 23 | 17 | 162 |

### Relation Type Breakdown

| Relation Type | Train | Validation | Test | Total |
|:--------------|------:|-----------:|-----:|------:|
| Descriptor-of | 2,782 | 324 | 337 | 3,443 |
| Participant-material | 2,132 | 257 | 276 | 2,665 |
| Value-of | 1,715 | 207 | 217 | 2,139 |
| Condition-of | 1,539 | 251 | 195 | 1,985 |
| Coreference | 1,159 | 137 | 126 | 1,422 |
| Next-operation | 803 | 90 | 98 | 991 |
| Device-of-operation | 635 | 72 | 105 | 812 |
| Brand-of | 330 | 35 | 18 | 383 |

## Schema

The extraction schema defines 7 entity types (2 with subtypes) and 8 relation types:

### Entity Types

| Entity Type | Subtypes | Description | Example |
|:------------|:---------|:------------|:--------|
| `materials` | target, recipe, intermedium, others | Materials involved in synthesis | Li₁.₁Cu₀.₉S, CuS, ethanol |
| `operations` | — | Synthesis operations or process steps | obtained, pressed, annealed, stirred |
| `descriptors` | — | Qualitative descriptors | polycrystalline, anhydrous, powder |
| `values` | — | Quantitative values with units | 99.999%, 14 mm, 1:1 stoichiometry |
| `properties` | temperature, time, pressure, rate | Measured process properties | 900 °C, 10 h, 5 MPa, 2 °C/min |
| `devices` | — | Equipment or apparatus | Al₂O₃ tubes, furnace, crucible |
| `brands` | — | Manufacturer or supplier names | Sigma Aldrich, Alfa Aesar |

### Relation Types

| Relation Type | Direction | Description |
|:--------------|:----------|:------------|
| `Descriptor-of` | Descriptor → Entity | A descriptor qualifies an entity |
| `Value-of` | Value → Entity | A quantitative value is associated with an entity |
| `Brand-of` | Brand → Material | A brand/supplier provides a material |
| `Condition-of` | Property → Operation | A property serves as a condition for an operation |
| `Participant-material` | Material → Operation | A material participates in an operation |
| `Device-of-operation` | Device → Operation | A device is used in an operation |
| `Next-operation` | Operation → Operation | Sequential ordering of operations |
| `Coreference` | Entity → Entity | Two mentions refer to the same entity |

Full schema: [`data/schemas/PcMSP/PcMSP-schema.json`](../../schemas/PcMSP/PcMSP-schema.json)

## Citation

If you use this dataset, please cite the original PcMSP paper:

```bibtex
@inproceedings{yang2022pcmsp,
  title={Pcmsp: A dataset for scientific action graphs extraction from polycrystalline materials synthesis procedure text},
  author={Yang, Xianjun and Zhuo, Ya and Zuo, Julia and Zhang, Xinlu and Wilson, Stephen and Petzold, Linda},
  booktitle={Findings of the Association for Computational Linguistics: EMNLP 2022},
  pages={6033--6046},
  year={2022}
}
```

## Source

- **Source:** [PcMSP Dataset](https://github.com/Xianjun-Yang/PcMSPP)