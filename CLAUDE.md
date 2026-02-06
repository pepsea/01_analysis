# CLAUDE.md

## Project Overview

This is a **bioinformatics/computational biology analysis repository** (part of the PEPSEA project) focused on protein and peptide sequence analysis. The work is organized in dated directories containing Jupyter notebooks and supporting data files.

### Domain Areas

- **Neoantigen detection** — cancer immunotherapy analysis identifying novel tumor antigens
- **Protein subcellular localization prediction** — predicting where proteins localize within cells using the DeepLoc dataset

## Repository Structure

```
01_analysis/
├── CLAUDE.md              # This file
├── README.md              # Project README (minimal)
├── 20250216/              # Analysis directory (YYYYMMDD date format)
│   ├── neoantigen001.ipynb        # Neoantigen analysis notebook
│   ├── proteinlocalization01.ipynb # Protein localization notebook
│   └── data/
│       └── deeploc_data.fasta     # DeepLoc protein sequence dataset (~28K sequences)
```

## Tech Stack

- **Language:** Python 3.13+
- **Notebook environment:** Jupyter (kernel: `venv01`)
- **Key libraries:**
  - `numpy`, `pandas` — data manipulation
  - `torch` (PyTorch) — deep learning (nn, optim, utils.data)
  - `scikit-learn` — metrics (accuracy_score)
  - `torchmetrics` — precision, recall
  - `matplotlib` — visualization
  - `BioPython` (`Bio.Seq`) — biological sequence handling

## Development Workflow

### Environment Setup

The project uses a Python virtual environment (`venv01`). There is no `requirements.txt` or `pyproject.toml` — dependencies must be installed manually:

```bash
pip install numpy pandas torch scikit-learn torchmetrics matplotlib biopython
```

### Running Notebooks

Open and run notebooks with Jupyter:

```bash
jupyter notebook 20250216/neoantigen001.ipynb
```

### No Build System

This is an analysis-focused repository. There is no build system, CI/CD pipeline, or automated testing.

## Conventions

### Directory Naming

- Analysis directories use `YYYYMMDD` date format (e.g., `20250216/`)
- Data files go in a `data/` subdirectory within each analysis directory

### Notebook Naming

- Notebooks follow the pattern: `<analysis_topic><sequence_number>.ipynb`
- Examples: `neoantigen001.ipynb`, `proteinlocalization01.ipynb`

### Data Formats

- Protein sequence data uses FASTA format (`.fasta`)
- FASTA headers contain protein IDs and localization annotations (e.g., `>Q9H400 Cell.membrane-M test`)

### Code Style

- Standard Python scientific computing conventions
- Imports grouped at top of notebooks: standard library, then third-party
- PyTorch used for neural network models
- No formal linting or formatting configuration — follow PEP 8

## Important Notes for AI Assistants

1. **No `.gitignore` exists** — be careful not to commit sensitive files, virtual environments, or large generated artifacts
2. **Large data files are tracked in git** — the FASTA file (~7.6 MB) is version-controlled; consider whether new large files should be added
3. **No tests or CI** — when adding functionality, consider whether test coverage would be appropriate
4. **No dependency management** — if adding new dependencies, document them clearly
5. **Notebook-first workflow** — primary analysis happens in Jupyter notebooks, not standalone Python scripts
6. **Research/exploratory code** — this is analysis code, not production software; prioritize clarity and correctness over engineering abstractions
