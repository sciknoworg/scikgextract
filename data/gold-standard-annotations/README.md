# Gold-Standard Annotations

Domain-expert manual annotations used as the benchmark for evaluating ALD extraction results. These differ from the public benchmark datasets in `gold-standard-datasets/` — they were created specifically for this project.

## Contents

### `ALD/experimental-usecase/`

Annotations for Atomic Layer Deposition (ALD) processes covering ZnO and IGZO materials from the AtomicLimits Database.

| File / Folder | Description |
|---|---|
| `AnnotatedData_IGZO_ZnO.xlsx` | Combined Excel spreadsheet with domain-expert annotations for both ZnO and IGZO processes |
| `ZnO/annotated_data_without_figure.json` | JSON export of ZnO annotations (figure data excluded) |
| `IGZO/annotated_data_without_figures.json` | JSON export of IGZO annotations (figure data excluded) |

### Annotated Fields

Each annotated entry captures the following process properties:

- **Material deposited** — target thin-film material (e.g. `ZnO`, `IGZO`)
- **Precursor(s)** — chemical precursor(s) used in the ALD cycle
- **Co-reactant(s)** — oxidant or reactant paired with the precursor
- **Process parameters** — deposition temperature, number of cycles, growth rate, etc.

> [!NOTE]
> These annotations cover only the experimental use-case subset (ZnO and IGZO from the AtomicLimits Database).
