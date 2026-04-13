# BioRED — a rich biomedical relation extraction dataset

## Overview

**BioRED** is a gold-standard dataset for biomedical entity and relation extraction from PubMed abstracts. It provides multi-type entity annotations with database identifiers and document-level relation annotations between entity pairs, including a novelty flag indicating whether the relation was previously reported in the literature. BioRED covers a broad range of biomedical entity types and relation types, making it one of the most comprehensive biomedical RE datasets.

- **Domain:** Biomedical
- **Source:** PubMed abstracts
- **Annotation Level:** Document-level (entity mentions with DB identifiers + document-level relations)
- **Splits:** Train / Validation / Test

## Dataset Statistics

### Summary

| Split | Documents | Entities | Relations | Novel Relations |
|:------|----------:|---------:|----------:|----------------:|
| Train | 400 | 13,351 | 4,178 | 2,838 (67.9%) |
| Validation | 100 | 3,533 | 1,162 | 835 (71.9%) |
| Test | 100 | 3,535 | 1,163 | 859 (73.9%) |
| **Total** | **600** | **20,419** | **6,503** | **4,532 (69.7%)** |

### Entity Type Breakdown

| Entity Type | Train | Validation | Test | Total |
|:------------|------:|-----------:|-----:|------:|
| GeneOrGeneProduct | 4,430 | 1,087 | 1,180 | 6,697 |
| DiseaseOrPhenotypicFeature | 3,646 | 982 | 917 | 5,545 |
| ChemicalEntity | 2,853 | 822 | 754 | 4,429 |
| OrganismTaxon | 1,429 | 370 | 393 | 2,192 |
| SequenceVariant | 890 | 250 | 241 | 1,381 |
| CellLine | 103 | 22 | 50 | 175 |

### Relation Type Breakdown

| Relation Type | Train | Validation | Test | Total |
|:--------------|------:|-----------:|-----:|------:|
| Association | 2,192 | 560 | 635 | 3,387 |
| Positive_Correlation | 1,089 | 352 | 325 | 1,766 |
| Negative_Correlation | 763 | 216 | 171 | 1,150 |
| Bind | 61 | 19 | 9 | 89 |
| Cotreatment | 31 | 10 | 14 | 55 |
| Comparison | 28 | 5 | 6 | 39 |
| Drug_Interaction | 11 | 0 | 2 | 13 |
| Conversion | 3 | 0 | 1 | 4 |

## Schema

The extraction schema defines 6 entity types and 8 relation types:

### Entity Types

| Entity Type | Description | DB Identifier |
|:------------|:------------|:--------------|
| `GeneOrGeneProduct` | Genes, proteins, and gene products | NCBI Gene ID |
| `DiseaseOrPhenotypicFeature` | Diseases and phenotypic features | MeSH ID, OMIM |
| `ChemicalEntity` | Chemical compounds and drugs | MeSH ID |
| `SequenceVariant` | DNA/protein sequence variants | dbSNP RS#, HGVS notation |
| `OrganismTaxon` | Organism species and taxa | NCBI Taxonomy ID |
| `CellLine` | Cell line names | Cellosaurus ID |

### Relation Types

| Relation Type | Description |
|:--------------|:------------|
| `Association` | General association between two entities |
| `Positive_Correlation` | Positive correlation or upregulation |
| `Negative_Correlation` | Negative correlation or downregulation |
| `Bind` | Physical binding interaction |
| `Comparison` | Comparative relationship |
| `Conversion` | Biochemical conversion |
| `Cotreatment` | Entities applied together as treatment |
| `Drug_Interaction` | Drug-drug interaction |

Each relation also carries a **novelty flag** (`novel: true/false`) indicating whether the relation was newly reported in the annotated abstract or was already known from prior literature.

Full schema: [`data/schemas/BioRED/BioRED-schema.json`](../../schemas/BioRED/BioRED-schema.json)

## Citation

If you use this dataset, please cite the original BioRED paper:

```bibtex
@article{luo2022biored,
  title={BioRED: a rich biomedical relation extraction dataset},
  author={Luo, Ling and Lai, Po-Ting and Wei, Chih-Hsuan and Arighi, Cecilia N and Lu, Zhiyong},
  journal={Briefings in Bioinformatics},
  volume={23},
  number={5},
  pages={bbac282},
  year={2022},
  publisher={Oxford University Press}
}
```

## Source

- **Source:** [BioRED at NCBI](https://ftp.ncbi.nlm.nih.gov/pub/lu/BioRED/)