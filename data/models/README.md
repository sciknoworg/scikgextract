# Models

Pydantic models that define the expected structure of inputs and outputs at each stage of the SciKGExtract pipeline. These models provide schema validation and type safety for LLM responses, API calls, and normalization results.

> [!NOTE]
> `models/schema/` defines Python-side Pydantic classes for structured extraction outputs. The corresponding LLM-facing JSON Schema files live in `data/schemas/`.

## Sub-modules

### `api/` — External API Response Models

Models for deserializing PubChem API responses used during chemical entity normalization.

| File | Class(es) | Description |
|---|---|---|
| `pubchem_property.py` | `PropertyItem`, `PropertyTable`, `PubChemPropertyResponse` | Chemical property response from the PubChem REST API |
| `pubchem_synonyms.py` | `InformationItem`, `InformationList`, `PubChemSynonymsResponse` | Synonym lookup response from the PubChem REST API |

### `evaluation/` — LLM Evaluation Response Models

Models for structured outputs returned by LLM judges during the reflection/evaluation step.

| File | Class | Description |
|---|---|---|
| `critic_response.py` | `CriticResponse` | Structured critique produced by a judge LLM |
| `evaluation_rating.py` | `EvaluationRating` | Numerical rating with justification from a judge LLM |

### `normalization/` — Normalization Response Models

| File | Class | Description |
|---|---|---|
| `llm_disambiguation.py` | `LLM_Disambiguation` | Structured output for LLM-based entity disambiguation for chemical names |

### `schema/` — Extraction Output Schemas (Pydantic)

Domain-specific Pydantic models that define the structured output the LLM is expected to produce. Used for response validation and downstream processing.

| File | Domain | Top-level Class |
|---|---|---|
| `ALD_experimental_schema.py` | ALD (experimental) | — |
| `ALD_experimental_schema_normalized.py` | ALD (experimental, normalized) | — |
| `ALD_simulation_schema.py` | ALD (simulation) | — |
| `bc5cdr_schema.py` | BC5CDR | `BC5CDRSchema` |
| `biored_schema.py` | BioRED | `BioREDSchema` |
| `pcmsp_schema.py` | PcMSP | `PcMSPSchema` |
| `polyie_schema.py` | PolyIE | `PolyIESchema` / `PolyIESchemaList` |
