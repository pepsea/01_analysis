# CLAUDE.md

## Project Overview

Bioinformatics analysis repository focused on peptide/protein computational analysis. The primary functionality is peptide molecular weight calculation, with early-stage notebooks for neoantigen analysis and protein subcellular localization prediction.

**Primary language:** Python 3
**Documentation language:** Japanese (code comments, docstrings, and notebook markdown are in Japanese)

## Repository Structure

```
/
├── peptide_mw.py                   # Core module: peptide molecular weight calculations
├── peptide_molecular_weight.ipynb  # Main notebook: MW calculation demos and batch analysis
├── 20250216/                       # Analysis notebooks and datasets (dated directory)
│   ├── data/
│   │   └── deeploc_data.fasta     # Protein sequence dataset (~28k lines, ~7.6MB)
│   ├── neoantigen001.ipynb        # Neoantigen analysis (early stage, imports only)
│   └── proteinlocalization01.ipynb # Protein localization (early stage, placeholder)
├── README.md                       # Minimal project readme
├── .gitignore                      # Ignores __pycache__/, *.pyc, .ipynb_checkpoints/
└── CLAUDE.md                       # This file
```

## Key Module: peptide_mw.py

Standalone Python module (no external dependencies) providing:

- `calculate_mw(sequence, mass_type, modifications)` — Peptide molecular weight from amino acid sequence (monoisotopic or average mass)
- `calculate_mz(sequence, charge, mass_type, modifications)` — m/z value for mass spectrometry
- `amino_acid_composition(sequence)` — Amino acid frequency analysis
- `sequence_summary(sequence, mass_type)` — Combined summary with MW, m/z at charges 1-3, and composition

Constants defined: `MONOISOTOPIC_MASS`, `AVERAGE_MASS`, `WATER_MONOISOTOPIC`, `WATER_AVERAGE`, `MODIFICATIONS` (9 common post-translational modifications).

Sequences use standard single-letter amino acid codes (20 standard amino acids). Input is normalized to uppercase with whitespace/newlines stripped.

## Running the Code

```bash
# Run the module directly (prints example calculations for test peptides)
python peptide_mw.py

# Launch Jupyter notebooks
jupyter notebook peptide_molecular_weight.ipynb
```

## Dependencies

### Core module (peptide_mw.py)
- **None** — uses only Python standard library

### Notebooks
- pandas
- numpy
- matplotlib
- jupyter

### 20250216/neoantigen001.ipynb (future work)
- pytorch (torch)
- scikit-learn
- torchmetrics
- biopython (Bio)

**Note:** There is no `requirements.txt`, `pyproject.toml`, or formal dependency management. Install dependencies manually as needed.

## Development Conventions

- **No formal test suite** — no pytest/unittest configuration exists. The `if __name__ == "__main__"` block in `peptide_mw.py` serves as a basic smoke test.
- **No linter/formatter configured** — no black, flake8, pylint, or similar tooling.
- **No CI/CD** — no GitHub Actions or other pipeline configuration.
- **Dated subdirectories** (e.g., `20250216/`) are used to organize analysis batches.
- **FASTA files** in `data/` directories contain protein sequences for batch processing.
- Docstrings follow NumPy-style format with Japanese descriptions.
- Error messages are in Japanese.

## Git Workflow

- Remote: `origin` (GitHub via proxy)
- Primary branch: `main`
- Feature branches use `claude/` prefix (e.g., `claude/peptide-molecular-weight-Gcz9b`)
- Merge via pull requests

## Important Notes for AI Assistants

- Preserve Japanese in all comments, docstrings, error messages, and notebook markdown when editing existing code.
- `peptide_mw.py` is intentionally dependency-free — do not add external package imports to it.
- The `20250216/data/deeploc_data.fasta` file is large (~7.6MB). Do not read it entirely; use `parse_fasta()` with `max_sequences` limit.
- Some FASTA sequences contain non-standard amino acid characters (e.g., `U` for selenocysteine, `X` for unknown) which will raise `ValueError` in `calculate_mw()` — this is expected behavior.
- Notebooks may reference local file paths relative to the repo root.
