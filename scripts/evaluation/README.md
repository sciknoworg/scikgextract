# Evaluation Scripts

Scripts for evaluating structured knowledge extracted by the SciKGExtract pipeline against gold-standard datasets or using LLM-as-a-Judge.

## Scripts

| Script | Dataset | Evaluation Type |
|---|---|---|
| `evaluate_bc5cdr.py` | BC5CDR | Entity (token/span) + Relation P/R/F1 |
| `evaluate_biored.py` | BioRED | Entity (token/span) + Relation P/R/F1 |
| `evaluate_pcmsp.py` | PcMSP | Entity (token/span) + Relation P/R/F1 |
| `evaluate_polyie.py` | PolyIE | Entity (token/span) + Relation P/R/F1 |
| `evaluate_zno_igzo.py` | AtomicLimits | Per-field P/R/F1 against AtomicLimits folder-encoded annotations |
| `llm_as_a_judge_evaluation.py` | ALD/ALE papers | LLM-as-a-Judge using Correctness + Completeness rubrics |
| `compare_extracted_data_with_atomiclimits.py` | ALD/ALE papers | Field-level comparison against AtomicLimits database |

## Usage

### NLP Dataset Evaluation (BC5CDR / BioRED / PcMSP / PolyIE)

```bash
python scripts/evaluation/evaluate_bc5cdr.py \
    --llm_model "gpt-4o" \
    --experiment "experiment1" \
    --include_keys "text,type" \
    --relation_keys "type,chemical,disease" \
    --output "results/evaluation/BC5CDR/experiment1/gpt-4o_evaluation_summary.json"
```

**Arguments:**

| Argument | Default | Description |
|---|---|---|
| `--llm_model` | `ministral-3b-2512` | Name of the LLM model whose extractions to evaluate |
| `--experiment` | `experiment2` | Experiment folder name to evaluate (e.g., `experiment1`) |
| `--include_keys` | `text,type` | Comma-separated entity keys to include in evaluation |
| `--exclude_keys` | None | Comma-separated entity keys to exclude |
| `--relation_keys` | `type,chemical,disease` | Comma-separated keys for relation evaluation |
| `--output` | Auto-generated path | Path to save the evaluation summary JSON |

> `evaluate_biored.py`, `evaluate_pcmsp.py`, and `evaluate_polyie.py` accept the same arguments, adjusting defaults for their respective datasets.

### ZnO/IGZO Evaluation

```bash
python scripts/evaluation/evaluate_zno_igzo.py \
    --llm_model "gpt-4o" \
    --material "ZnO"
```

The script reads extraction results from `results/extractions/`, derives gold-standard annotations from AtomicLimits folder names (format: `"Precursor - Coreactant"`), and computes per-field P/R/F1 scores. Optionally computes BERTScore using `allenai/scibert_scivocab_uncased`.

### LLM-as-a-Judge Evaluation

```bash
python scripts/evaluation/llm_as_a_judge_evaluation.py \
    --llm_model "OPENAI:gpt-4o" \
    --extracted_data_path "results/extractions/ALD/ZnO-IGZO-papers" \
    --scientific_document_path "data/research-papers/ALD/markdown" \
    --results_dir "results/evaluation/ALD/llm-as-judge" \
    --process_schema_path "data/schemas/ALD/ALD-schema.json"
```

Uses the `Correctness` and `Completeness` rubrics from `scikg_extract.evaluation.rubrics.informativeness` to score each extraction against the source document.

### AtomicLimits Comparison

```bash
python scripts/evaluation/compare_extracted_data_with_atomiclimits.py \
    --input "results/extractions/ALD/AtomicLimits" \
    --output "results/evaluation/ALD/atomiclimits_comparison.json"
```

## Output Format

All evaluation scripts output a JSON file with per-field and aggregated metrics:

```json
{
  "precision": 0.85,
  "recall": 0.78,
  "f1": 0.81,
  "per_field": {
    "material_deposited": {"precision": 1.0, "recall": 1.0, "f1": 1.0},
    "precursor": {"precision": 0.82, "recall": 0.74, "f1": 0.78}
  }
}
```

## Dependencies

- `scikg_extract.evaluation.metrics` — shared P/R/F1 computation and aggregation utilities
- `bert_score` — optional, required only for BERTScore computation
