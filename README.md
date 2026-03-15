# Reference Toolkit

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A comprehensive tool for discovering, validating, resolving, and downloading academic papers.

## Features

| Feature | Description |
|---------|-------------|
| **Search** | Find papers via Google Scholar, PubMed, Crossref |
| **Parse** | Import EndNote, Mendeley, BibTeX, RIS exports |
| **Resolve** | Match citations to DOIs via Crossref |
| **Validate** | Detect fake/incomplete references |
| **Download** | Get open-access PDFs via Unpaywall |
| **Export** | Output to BibTeX, CSV, JSON |

## Installation

```bash
pip install reference-toolkit
```

Or from source:

```bash
git clone https://github.com/your-repo/reference-toolkit.git
cd reference-toolkit
pip install -e .
```

## Quick Start

```bash
# Search for papers
reftool search "machine learning protein folding" --limit 20

# Resolve references to DOIs
reftool resolve refs.txt

# Download open-access PDFs
reftool download resolved_refs.csv

# Full pipeline (resolve + download + BibTeX export)
reftool pipeline refs.bib --bibtex
```

## Commands

### `search` - Find Papers

```bash
reftool search "CRISPR gene editing" \
    --source pubmed \
    --year-start 2020 \
    --year-end 2024 \
    --limit 50 \
    --output results.csv
```

Options:
- `--source`: `all` (default), `scholar`, `pubmed`, `crossref`
- `--format`: `csv` (default), `bibtex`, `json`
- `--year-start` / `--year-end`: Filter by publication year
- `--limit`: Max results per source

### `resolve` - Match Citations to DOIs

```bash
reftool resolve refs.txt \
    --output resolved.csv \
    --confidence 60 \
    --max-results 3
```

Accepts: `.txt` (EndNote/Mendeley), `.bib`, `.ris`

Options:
- `--confidence`: Score threshold (default: 60)
- `--resume`: Skip already-processed refs
- `--max-results`: Show top N matches for review

### `download` - Get Open-Access PDFs

```bash
reftool download resolved.csv \
    --download-dir pdfs/ \
    --resume
```

Options:
- `--resume`: Skip existing PDFs
- `--no-update`: Don't modify input CSV

### `pipeline` - Full Workflow

```bash
reftool pipeline refs.txt \
    --output-csv resolved.csv \
    --download-dir pdfs/ \
    --bibtex \
    --mailto your@email.com
```

Runs: parse → resolve → download → export

### `convert` - Format Conversion

```bash
reftool convert refs.txt --output refs.bib --format bibtex
reftool convert refs.bib --output refs.csv --format csv
```

### `contacts` - Author Contact Extraction

```bash
reftool contacts resolved_refs.csv -o author_requests.txt
```

Extracts corresponding author emails and generates request emails for papers you couldn't download.

### `rename` - Batch Rename PDF Files

```bash
# Rename PDFs in a folder based on their metadata
reftool rename pdfs_to_rename/

# Preview what would be renamed (dry run)
reftool rename pdfs_to_rename/ --dry-run

# Copy renamed files to new directory (keeps originals)
reftool rename pdfs/ --output-dir renamed_pdfs/
```

Extracts metadata (title, authors, year) from PDF files and renames them with human-readable filenames in the format: `{Author}_{Year}_{Title}.pdf`

## Enhanced Features

- **Semantic Scholar Integration**: Finds PDFs missed by Unpaywall
- **PDF Quality Validation**: Checks for corrupted, encrypted, or scanned PDFs
- **Smart Rate Limiting**: Respects API quotas with exponential backoff
- **Title-Based Filenames**: PDFs named as `{Author}_{Year}_{Title}.pdf`
- **Preprint Search**: Searches arXiv, bioRxiv, medRxiv, PMC for OA versions

## Input Formats

| Format | Extension | Auto-detected |
|--------|-----------|---------------|
| EndNote plain text | `.txt` | ✅ |
| Mendeley plain text | `.txt` | ✅ |
| BibTeX | `.bib` | ✅ |
| RIS | `.ris` | ✅ |
| DOI list | `.txt` | ✅ |

## Output Files

| File | Description |
|------|-------------|
| `resolved_refs.csv` | Main output with DOIs and metadata |
| `unresolved_refs.csv` | References without matches |
| `low_confidence_refs.csv` | Suspicious matches (check manually) |
| `pdfs/` | Downloaded open-access PDFs |
| `*.log` | Detailed operation logs |

## CSV Columns

| Column | Description |
|--------|-------------|
| `raw_citation` | Original reference text |
| `title` | Resolved title |
| `doi` | Digital Object Identifier |
| `authors` | Author list |
| `year` | Publication year |
| `journal` | Journal/conference name |
| `crossref_score` | Match confidence score |
| `confidence_flag` | `ok` or `low` |
| `pdf_downloaded` | `yes`, `no`, or `failed` |
| `oa_status` | `gold`, `green`, `hybrid`, `closed` |

## Validation Workflow

Use the tool to validate references:

```bash
# Check if references are real
reftool resolve refs.txt --confidence 60

# Review low-confidence matches
cat low_confidence_refs.csv

# High score (>60) = likely valid
# Low score (<60) = check manually
# No match = possibly fake
```

## Typical Workflows

### Literature Review

```bash
# 1. Search for papers
reftool search "CRISPR therapeutic" --source pubmed --limit 100 --output search.csv

# 2. Add your existing references
cat my_refs.txt >> all_refs.txt

# 3. Resolve all to DOIs
reftool resolve all_refs.txt --output final_refs.csv

# 4. Download available PDFs
reftool download final_refs.csv --download-dir pdfs/

# 5. Export to BibTeX
reftool convert final_refs.csv --output references.bib --format bibtex
```

### Reference Validation

```bash
# Check a list of references for validity
reftool resolve refs.txt --max-results 3

# Check low-confidence matches
cat low_confidence_refs.csv

# Scores:
#   >80: Very likely correct
#   60-80: Probably correct
#   <60: Check manually
#   No match: Possibly fake/incorrect
```

### Mendeley/EndNote Export

```bash
# Export from Mendeley as BibTeX, then:
reftool resolve library.bib --bibtex

# Export from EndNote as text, then:
reftool pipeline exported_refs.txt
```

## API Etiquette

This tool respects API usage policies:

- Requires `--mailto` email for API access
- Rate limiting between requests
- Handles 429 responses with backoff
- Only retrieves open-access PDFs (no paywall bypass)

## Importing into EndNote/Mendeley

1. **EndNote**: File → Import → Folder... → Select `pdfs/` → Import Option: PDF
2. **Mendeley**: File → Add Files... → Select `pdfs/` folder

## Dependencies

- `requests` - HTTP requests
- `bibtexparser` - BibTeX parsing
- `scholarly` - Google Scholar access

## License

MIT License
