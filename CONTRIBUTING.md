# Contributing to SciKGExtract

Thank you for your interest in contributing to **SciKGExtract** — an agentic framework for structured scientific knowledge extraction from research papers. This project is primarily a research endeavour, and contributions that advance its scientific and engineering quality are welcome.

Please read this guide carefully before submitting any contribution. By participating in this project you agree to abide by its [Apache License 2.0](LICENSE).

---

## Table of Contents

1. [How to Contribute](#how-to-contribute)
2. [Development Setup](#development-setup)
3. [Submitting a Pull Request](#submitting-a-pull-request)
4. [Code Guidelines](#code-guidelines)
5. [Questions](#questions)

---

## How to Contribute

We welcome the following types of contributions:

### Bug Reports
If you encounter unexpected behaviour, please open a [GitHub Issue](https://github.com/sciknoworg/SciKG-extract/issues) and include:
- A clear, concise description of the problem
- Steps to reproduce (script command, notebook cell, or pipeline configuration)
- Relevant log output from `logs/` or terminal output
- Your environment details (OS, Python version, conda env, LLM provider)

### Feature Requests
Suggestions for new capabilities are welcome via GitHub Issues. Useful feature requests include:
- Support for new LLM providers (beyond OpenAI, SAIA, Ollama, HuggingFace)
- New dataset or domain adapters
- New pipeline variants or evaluation strategies
- etc.

### Domain Schema Additions
If you wish to apply SciKGExtract to a new scientific domain, you may contribute a JSON Schema that describes your target data model. New schemas should be placed under `data/schemas/<domain>/` and must validate correctly with `jsonschema`.

---

## Development Setup

Follow these steps to set up a local development environment.

**1. Clone the repository**
```bash
git clone https://github.com/sciknoworg/scikgextract.git
cd scikgextract
```

**2. Create and activate the conda environment**
```bash
conda create -n env python=3.12 -y
conda activate env
```

**3. Install the package in editable mode**
```bash
pip install -e .
```

**4. Set the Python path**

Scripts and notebooks expect the repository root to be on `PYTHONPATH`:
```bash
# Linux / macOS
export PYTHONPATH=$(pwd)

# Windows PowerShell
$env:PYTHONPATH = "$PWD"
```

**5. Configure API keys**

Create a `.env` file in the repository root based on the required credentials for your target LLM providers:
```
OPENAI_API_KEY=your_openai_key
SAIA_API_KEY=your_saia_key
```

**6. Install pre-commit hooks**
```bash
pip install pre-commit
pre-commit install
```

This installs the hooks defined in `.pre-commit-config.yaml` (ruff, mypy, bandit, and standard file checks). The hooks will run automatically on every `git commit`.

---

## Submitting a Pull Request

**1. Fork the repository** and create a feature branch from `main`:
```bash
git checkout -b feat/your-descriptive-branch-name
```
Branch naming conventions:
- `feat/` — new feature or capability
- `fix/` — bug fix
- `docs/` — documentation-only change
- `refactor/` — code restructuring without behaviour change

**2. Make focused, well-scoped changes.** Each pull request should address a single concern. Large, unrelated changes are harder to review and slower to merge.

**3. Run pre-commit checks locally** before pushing:
```bash
pre-commit run --all-files
```
All ruff, mypy, and bandit checks must pass before a PR will be reviewed.

**4. Push your branch and open a pull request** against `main` on GitHub. In the PR description, please include:
- A summary of what was changed and why
- How to verify or test the change (e.g. script command, expected output)
- A reference to any related GitHub Issue (e.g. `Closes #42`)

**5. Request a review** from one of the project maintainers (see [Questions](#questions)). Expect feedback within a reasonable timeframe; this is a research project and review times may vary.

---

## Code Guidelines

Please follow these conventions when writing code for SciKGExtract:

### Language and Runtime
- Python **≥ 3.12** is required. Do not use syntax or APIs unavailable in 3.12.

### Type Annotations
- All public functions and methods must have complete type annotations for parameters and return values.
- Use standard library types (`list`, `dict`, `str | None`) rather than `typing.List`, `typing.Dict`, etc.

### Linting and Formatting
- Code style is enforced by **ruff**. Run `ruff check --fix .` to auto-fix issues before committing.
- Do not disable ruff rules without a clearly documented reason (`# noqa: <code>  # reason`).

### Type Checking
- **mypy** is configured as a pre-commit hook. All new code must pass mypy without errors.
- Add type stubs (e.g. `types-PyYAML`) for third-party packages that lack inline annotations.

### Security
- **bandit** scans for medium- and high-severity security issues. All flagged issues must be resolved before merging.
- Do not hard-code credentials or API keys. Use environment variables loaded via `python-dotenv`.

### LLM Provider Convention
- LLM models must be identified using the `PROVIDER:model` string convention (e.g. `OPENAI:gpt-4o`, `SAIA:anthropic/claude-sonnet-4.6`). Do not introduce ad-hoc identifier formats.

### JSON Schemas
- New or modified schemas under `data/schemas/` must be valid JSON Schema (Draft-07 or later) and must be verified with `jsonschema` before submission.

### Data and Binary Files
- Do not commit data files larger than 5 MB. Use external storage or document a download procedure in `data/README.md`.
- Do not commit model weights, embeddings, or LMDB databases.

### Scripts and Notebooks
- Extraction scripts under `scripts/` must be executable independently from the repository root with `PYTHONPATH` set.
- Notebooks under `notebooks/` must be re-runnable top-to-bottom in a clean kernel.

---

## Questions

For bug reports and feature requests, please use [GitHub Issues](https://github.com/sciknoworg/scikgextract/issues).

For questions about the research methodology, collaboration opportunities, or anything not suited for a public issue, please contact the project maintainers directly:

| Maintainer | Email |
|---|---|
| Jennifer D'Souza | jennifer.dsouza@tib.eu |
| Sameer Sadruddin | sameer.sadruddin@tib.eu |

Response times may vary as this is an active research project.
