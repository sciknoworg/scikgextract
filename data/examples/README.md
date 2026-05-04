# Examples

Few-shot examples injected into LLM prompts at inference time to guide the model toward the expected extraction format and values.

## Format

Each example file (`example1.txt`) contains two sections:

- **Input Text** — a representative source passage (abstract, sentence, or annotated document fragment)
- **Expected Output** — the correctly structured extraction corresponding to that input, either as JSON or as a field-by-field YAML-like listing

## Contents

| Domain | Path | Demonstrates |
|---|---|---|
| ALD — ZnO | `ALD/ZnO/example1.txt` | ALD process parameter extraction for ZnO (precursor, co-reactant, conditions) |
| ALD — IGZO | `ALD/IGZO/example1.txt` | ALD process parameter extraction for IGZO (multi-precursor systems) |
| BC5CDR | `BC5CDR/example1.txt` | Chemical and disease entity extraction with MeSH identifiers and CID relations |
| BioRED | `BioRED/example1.txt` | Multi-type biomedical entity and relation extraction |
| PcMSP | `PcMSP/example1.txt` | Materials synthesis operation and property extraction |
| PolyIE | `PolyIE/example1.txt` | Polymer chemical name, property, and value extraction |

## Usage

Pass an example file to the extraction script via `--process_examples`, for instance:

```bash
python scripts/knowledge_extraction/<domain>/information_extraction.py \
    --process_examples data/examples/<domain>/example1.txt \
    ...
```

To add a new example for an existing domain, replace or extend the relevant `example1.txt`. To support a new domain, create a new subfolder following the same two-section format.
