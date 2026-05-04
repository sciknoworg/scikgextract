# Schemas

JSON Schema files that define the structured output format the LLM is expected to produce. These are passed directly to the extraction pipeline at runtime to constrain and validate LLM responses.

> [!NOTE]
> These are **JSON Schema** files (LLM-facing). The corresponding **Pydantic** models for Python-side validation live in `data/models/schema/`.

## Contents

| Domain | Schema File | Corresponding Pydantic Model |
|---|---|---|
| ALD (experimental) | `ALD/experimental-usecase/ALD-experimental-schema.json` | `ALD_experimental_schema.py` |
| ALD (simulation) | `ALD/simulation-usecase/ALD-simulation-schema.json` | `ALD_simulation_schema.py` |
| BC5CDR | `BC5CDR/BC5CDR-schema.json` | `bc5cdr_schema.py` |
| BioRED | `BioRED/BioRED-schema.json` | `biored_schema.py` |
| PcMSP | `PcMSP/PcMSP-schema.json` | `pcmsp_schema.py` |
| PolyIE | `PolyIE/PolyIE-schema.json` | `polyie_schema.py` |

## Usage

Pass a schema file to any extraction script via `--process_schema`:

```bash
python scripts/knowledge_extraction/<domain>/information_extraction.py \
    --process_schema data/schemas/<domain>/<domain>-schema.json \
    ...
```

To add a new domain, create a subfolder with a JSON Schema file and a matching Pydantic model in `data/models/schema/`.
