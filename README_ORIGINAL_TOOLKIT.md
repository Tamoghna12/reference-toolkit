# Reference Toolkit

A command‑line toolkit for discovering, validating, resolving, and downloading academic references, with batch PDF renaming and export workflows tailored for researchers and systematic reviews.

> If you use this toolkit in your research, please see the **Citation** section below.

***

## 1. Overview

**Reference Toolkit** automates the end‑to‑end workflow around reference lists and PDFs:

- Searches multiple scholarly sources (Google Scholar, PubMed, Crossref, Semantic Scholar).  
- Parses exports from common reference managers (EndNote, Mendeley, BibTeX, RIS).  
- Resolves citations to DOIs and flags suspicious or incomplete references.  
- Downloads open‑access PDFs and renames them with human‑readable filenames.  
- Exports clean bibliographies to BibTeX, CSV, and JSON for downstream tools.

**Who is this for?**

- Researchers running literature reviews or meta‑analyses.  
- Students and supervisors managing large reference libraries.  
- Labs that want reproducible, scriptable reference management and validation.

***

## 2. Features at a glance

| Feature         | Description                                                 |
|----------------|-------------------------------------------------------------|
| **Search**     | Query Google Scholar, PubMed, Crossref                      |
| **Parse**      | Import EndNote, Mendeley, BibTeX, RIS exports               |
| **Resolve**    | Match citations to DOIs via Crossref                        |
| **Validate**   | Detect fake, low‑confidence, or incomplete references       |
| **Download**   | Retrieve open‑access PDFs via Unpaywall / Semantic Scholar  |
| **Export**     | Output to BibTeX, CSV, JSON                                 |
| **Rename**     | Batch rename PDFs as `{Author}_{Year}_{Title}.pdf`          |
| **Contacts**   | Extract corresponding author emails and draft requests      |

(You can leave out rows if you prefer a shorter table.)

***

## 3. Installation

### Quick start

For a fast setup, see:

- **[Quick Start](QUICK_START.md)** – minimal commands and first workflow  
- **[Installation Guide](INSTALL_GUIDE.md)** – platform‑specific details for Windows, macOS, and Linux  

### Install from PyPI (when available)

```bash
pip install reference-toolkit
```

### Install from source

```bash
git clone https://github.com/Tamoghna12/reference-toolkit.git
cd reference-toolkit
pip install -e .
```

### Docker (recommended for consistency)

```bash
docker build -t reference-toolkit:latest .
docker run --rm -v $(PWD):/data reference-toolkit:latest reftool --help
```

***

## 4. Quick start examples

The `reftool` CLI provides subcommands for common tasks.

```bash
# Search for papers
reftool search "machine learning protein folding" --limit 20

# Resolve references to DOIs
reftool resolve refs.txt

# Download open-access PDFs
reftool download resolved_refs.csv

# Full pipeline: resolve + download + BibTeX export
reftool pipeline refs.bib --bibtex
```

***

## 5. Core commands

### 5.1 `search` – find papers

```bash
reftool search "CRISPR gene editing" \
  --source pubmed \
  --year-start 2020 \
  --year-end 2024 \
  --limit 50 \
  --output results.csv
```

Key options:

- `--source`: `all` (default), `scholar`, `pubmed`, `crossref`  
- `--format`: `csv` (default), `bibtex`, `json`  
- `--year-start`, `--year-end`: filter by publication year  
- `--limit`: max results per source  

### 5.2 `resolve` – match citations to DOIs

```bash
reftool resolve refs.txt \
  --output resolved.csv \
  --confidence 60 \
  --max-results 3
```

Accepted input: `.txt` (EndNote/Mendeley style), `.bib`, `.ris`

Options:

- `--confidence`: score threshold (default: 60)  
- `--resume`: skip already‑processed references  
- `--max-results`: show top N matches for manual review  

### 5.3 `download` – get open‑access PDFs

```bash
reftool download resolved.csv \
  --download-dir pdfs/ \
  --resume
```

Options:

- `--resume`: skip existing PDFs  
- `--no-update`: do not modify the input CSV  

### 5.4 `pipeline` – end‑to‑end workflow

```bash
reftool pipeline refs.txt \
  --output-csv resolved.csv \
  --download-dir pdfs/ \
  --bibtex \
  --mailto your@email.com
```

Runs: parse → resolve → download → export.

### 5.5 `convert` – format conversion

```bash
reftool convert refs.txt --output refs.bib --format bibtex
reftool convert refs.bib --output refs.csv --format csv
```

### 5.6 `contacts` – author contact extraction

```bash
reftool contacts resolved_refs.csv -o author_requests.txt
```

Extracts corresponding author emails and generates request templates for inaccessible papers.

### 5.7 `rename` – batch PDF renaming

```bash
# Rename PDFs in-place based on metadata
reftool rename pdfs_to_rename/

# Preview changes without renaming
reftool rename pdfs_to_rename/ --dry-run

# Copy renamed files to a new directory
reftool rename pdfs/ --output-dir renamed_pdfs/
```

Filenames follow: `{Author}_{Year}_{Title}.pdf`.

***

## 6. Inputs, outputs, and columns

### Input formats

| Format              | Extension | Auto-detected |
|---------------------|-----------|---------------|
| EndNote plain text  | `.txt`    | ✅             |
| Mendeley plain text | `.txt`    | ✅             |
| BibTeX              | `.bib`    | ✅             |
| RIS                 | `.ris`    | ✅             |
| DOI list            | `.txt`    | ✅             |

### Output files

| File                  | Description                          |
|-----------------------|--------------------------------------|
| `resolved_refs.csv`   | Main output with DOIs + metadata     |
| `unresolved_refs.csv` | References without matches           |
| `low_confidence_refs.csv` | Suspicious matches to review    |
| `pdfs/`               | Downloaded open‑access PDFs          |
| `*.log`               | Detailed operation logs              |

### CSV columns

| Column            | Description                                  |
|-------------------|----------------------------------------------|
| `raw_citation`    | Original reference text                      |
| `title`           | Resolved title                               |
| `doi`             | Digital Object Identifier                    |
| `authors`         | Author list                                  |
| `year`            | Publication year                             |
| `journal`         | Journal or conference name                   |
| `crossref_score`  | Match confidence score                       |
| `confidence_flag` | `ok` or `low`                                |
| `pdf_downloaded`  | `yes`, `no`, or `failed`                     |
| `oa_status`       | `gold`, `green`, `hybrid`, or `closed`       |

***

## 7. Typical workflows

### 7.1 Literature review

```bash
# 1. Search for papers
reftool search "CRISPR therapeutic" \
  --source pubmed \
  --limit 100 \
  --output search.csv

# 2. Combine with existing references
cat my_refs.txt >> all_refs.txt

# 3. Resolve all references to DOIs
reftool resolve all_refs.txt --output final_refs.csv

# 4. Download available PDFs
reftool download final_refs.csv --download-dir pdfs/

# 5. Export to BibTeX
reftool convert final_refs.csv --output references.bib --format bibtex
```

### 7.2 Reference validation

```bash
# Check a list of references for validity
reftool resolve refs.txt --max-results 3

# Inspect low-confidence matches
cat low_confidence_refs.csv

# Rough interpretation:
#   >80: very likely correct
#   60–80: probably correct
#   <60: check manually
#   no match: possibly fake/incorrect
```

***

## 8. API etiquette and ethics

Reference Toolkit is designed to respect API usage policies:

- Requires `--mailto` email for some APIs.  
- Applies rate limiting and exponential backoff for HTTP 429.  
- Only retrieves open‑access PDFs (no paywall circumvention).  

Please be considerate when running large batch queries.

***

## 9. Reference managers: EndNote / Mendeley

You can import downloaded PDFs into your reference manager:

- **EndNote**: `File → Import → Folder…` → select `pdfs/` → Import Option: `PDF`.  
- **Mendeley**: `File → Add Files…` → select the `pdfs/` folder.  

***

## 10. Documentation

- **Installation & setup**  
  - [Quick Start](QUICK_START.md)  
  - [Installation Guide](INSTALL_GUIDE.md)  
  - [Docker Usage](docs/DOCKER_USAGE.md)  

- **Feature guides**  
  - [PDF Renaming Guide](docs/PDF_RENAMING_GUIDE.md)  
  - [Enhanced Features](docs/ENHANCED_ACCESS_FEATURES.md)  
  - [Future Enhancements](docs/FUTURE_ENHANCEMENTS.md)  

- **Development**  
  - [Contributing](CONTRIBUTING.md)  
  - [Changelog](CHANGELOG.md)  

***

## 11. Project structure

```text
reference-toolkit/
├── src/reference_toolkit/    # Source code
├── tests/                    # Test suite
├── examples/                 # Example scripts
├── docs/                     # Documentation
├── .github/workflows/        # CI/CD
├── Dockerfile                # Docker configuration
├── pyproject.toml            # Project configuration
└── requirements.txt          # Python dependencies
```

***

## 12. Development

### Running tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/reference_toolkit
```

### Code style

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

***

## 13. Dependencies

Key Python dependencies include:

- `requests` – HTTP requests  
- `bibtexparser` – BibTeX parsing  
- `scholarly` – Google Scholar access  
- `PyPDF2` – PDF metadata extraction  

***

## 14. Citation and license

If this toolkit contributes to your work, please cite it (example):

> Tamoghna Das, *Reference Toolkit* (Version 1.0.0), 2026.  
> DOI: `10.5281/zenodo.19051489`

- **License:** MIT – see [LICENSE](LICENSE) for details.  
