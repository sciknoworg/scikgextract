# Knowledge Extraction Scripts

Scripts for extracting structured knowledge from scientific documents using the SciKGExtract orchestration framework.

## Directory Structure

```
knowledge_extraction/
├── AtomicLimits Database/          # ALD (ZnO & IGZO) — AtomicLimits sub-corpus
│   ├── experiment1 - Extraction without Cleaning/
│   ├── experiment2 - Extraction with Cleaning/
│   ├── experiment3 - Extraction with Normalization/
│   └── experiment4 - Extraction with LLM-as-a-judge loop/
├── BC5CDR/                         # Chemical-Disease Relation extraction
│   ├── experiment1 - extraction/
│   ├── experiment2 - extraction with self-refinement/
│   ├── experiment3 - extraction with multi-judge-refinement/
│   └── experiment4 - extraction with debate-refinement/
├── BioRED/                         # Biomedical entity & relation extraction
│   ├── experiment1 - extraction/
│   ├── experiment2 - extraction with self-refinement/
│   ├── experiment3 - extraction with multi-judge-refinement/
│   └── experiment4 - extraction with debate-refinement/
├── PcMSP/                          # Materials synthesis procedure extraction
│   ├── experiment1 - extraction/
│   ├── experiment2 - extraction with self-refinement/
│   ├── experiment3 - extraction with multi-judge-refinement/
│   └── experiment4 - extraction with debate-refinement/
├── PolyIE/                         # Polymer property extraction
│   ├── experiment1 - extraction/
│   ├── experiment2 - extraction with self-refinement/
│   ├── experiment3 - extraction with multi-judge-refinement/
│   └── experiment4 - extraction with debate-refinement/
└── ZnO-IGZO-Papers/                # ALD (ZnO & IGZO) — full paper corpus
    ├── experiment1 - extraction without cleaning/
    ├── experiment2 - extraction with cleaning/
    ├── experiment3 - extraction with normalization/
    ├── experiment4 - extraction with self-refinement/
    ├── experiment5 - extraction with multi-judge-refinement/
    └── experiment6 - extraction with debate-refinement/
```

## CLI Arguments

### Experiments 1–3 (Extraction only / Cleaning / Normalization)

```bash
python scripts/knowledge_extraction/<domain>/<experiment>/<script>.py \
    --extraction_llm "PROVIDER:model_name" \
    --results_dir "results/extractions/<domain>/<experiment>" \
    --process_schema "data/schemas/<domain>/<schema>.json" \
    --process_examples "data/examples/<domain>/example1.txt" \
    --scientific_docs_dir "data/research-papers/<domain>/markdown"
```

For NLP datasets (BC5CDR, BioRED, PcMSP, PolyIE) replace `--scientific_docs_dir` with:

```
    --data_split "test"     # Options: train, val, test (default: test)
```

### Experiment 4 (Self-Refinement — single judge)

Adds reflection and feedback LLMs:

```bash
    --extraction_llm "PROVIDER:model_name" \
    --reflection_llm "PROVIDER:model_name" \
    --feedback_llm "PROVIDER:model_name"
```

### Experiment 5 (Multi-Judge Refinement)

Adds multiple judge LLMs and a summarizer:

```bash
    --extraction_llm "PROVIDER:model_name" \
    --reflection_judge_llms "PROVIDER:model1,PROVIDER:model2" \
    --summarizer_llm "PROVIDER:model_name" \
    --feedback_llm "PROVIDER:model_name"
```

### Experiment 6 (Debate-Style Refinement)

Adds critic LLMs in addition to judges and summarizer:

```bash
    --extraction_llm "PROVIDER:model_name" \
    --reflection_judge_llms "PROVIDER:model1,PROVIDER:model2" \
    --reflection_critic_llms "PROVIDER:critic1,PROVIDER:critic2" \
    --summarizer_llm "PROVIDER:model_name" \
    --feedback_llm "PROVIDER:model_name"
```

## Provider Format

LLM arguments use the format `PROVIDER:model_name`. Supported providers:

| Provider | Example |
|---|---|
| `OPENAI` | `OPENAI:gpt-4o`, `OPENAI:gpt-5` |
| `SAIA` | `SAIA:anthropic/claude-sonnet-4.6`, `SAIA:meta-llama/llama-3.3-70b-instruct` |
| `OLLAMA` | `OLLAMA:llama3:8b` |

## Output

Each script saves one JSON file per document to `--results_dir` under a subfolder named after the LLM model. Results follow the schema defined by the Pydantic data model for that domain (see `data/schemas/`).

## Example

```bash
# BC5CDR experiment3 — multi-judge refinement
python 'scripts/knowledge_extraction/BC5CDR/experiment3 - extraction with multi-judge-refinement/BC5CDR_information_extraction.py' \
    --extraction_llm "OPENAI:gpt-4o" \
    --reflection_judge_llms "OPENAI:gpt-5,SAIA:deepseek/deepseek-r1-0528" \
    --summarizer_llm "OPENAI:gpt-4o" \
    --feedback_llm "OPENAI:gpt-4o" \
    --data_split "test" \
    --results_dir "results/extractions/BC5CDR/experiment3/test" \
    --process_schema "data/schemas/BC5CDR/BC5CDR-schema.json" \
    --process_examples "data/examples/BC5CDR/example1.txt"
```
