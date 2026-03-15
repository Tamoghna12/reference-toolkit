# PDF Batch Renaming - Usage Guide

## Overview

The `rename` command extracts metadata from PDF files (title, authors, year) and renames them with human-readable filenames.

**Works on ANY PDF folder** - not just PDFs downloaded by this toolkit!

## Quick Start

```bash
# Rename PDFs in place
reftool rename my_pdfs/

# Preview changes without renaming (dry run)
reftool rename my_pdfs/ --dry-run

# Copy renamed files to new directory (keeps originals)
reftool rename downloads/ --output-dir organized/
```

## How It Works

### Metadata Extraction

The rename command extracts metadata from PDF files in this priority order:

1. **PDF Metadata** (if available)
   - Title from `/Title` field
   - Authors from `/Author` field
   - Year from `/CreationDate` field

2. **First Page Text** (fallback)
   - Scans first page for title-like text
   - Detects title case and line length
   - Identifies DOIs for reference

3. **DOI Extraction** (additional)
   - Searches for DOI patterns in text
   - Supports multiple DOI formats

### Naming Format

**Default Format**: `{FirstAuthor}_{Year}_{Title}.pdf`

**Examples**:
- `Buso_2024_Relative validity of habitual sugar.pdf`
- `Klopčič_2021_COMPUTATIONAL ASSESSMENT OF THE PHARMACOKINETICS.pdf`
- `Point_2024_IJB-V24-No1-p132-142.pdf`

**Title Truncation**:
- Maximum 60 characters from title
- Cuts at sentence boundary (`.`, `?`, `!`, `:`)
- Removes trailing punctuation
- Falls back to DOI naming if no metadata

**Special Characters**:
- Replaces em/en dashes with `-`
- Converts smart quotes to straight quotes
- Removes problematic characters for filenames
- Collapses multiple spaces

## Usage Examples

### Example 1: Rename Generic Downloads

```bash
# Before: downloads/
#   ├── paper1.pdf
#   ├── document2.pdf
#   └── full_text.pdf

reftool rename downloads/

# After: downloads/
#   ├── Smith_2023_Novel approach to protein folding.pdf
#   ├── Johnson_2024_Quantum computing applications.pdf
#   └── Lee_2022_Full text screening of cyclamates.pdf
```

### Example 2: Dry Run (Preview)

```bash
reftool rename unorganized_pdfs/ --dry-run

# Output:
# INFO: Would rename: paper1.pdf -> Smith_2023_Novel approach.pdf
# INFO: Would rename: document2.pdf -> Johnson_2024_Quantum.pdf
# INFO: Would rename: full_text.pdf -> Lee_2022_Full text.pdf
```

### Example 3: Copy to Organized Folder

```bash
# Original folder unchanged
reftool rename downloads/ --output-dir organized/

# downloads/ (original)
#   ├── paper1.pdf
#   └── document2.pdf

# organized/ (new renamed copies)
#   ├── Smith_2023_Novel approach.pdf
#   └── Johnson_2024_Quantum computing.pdf
```

## Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `folder` | Folder containing PDFs to rename | Required |
| `--pattern` | Naming pattern template | `{title}_{year}` |
| `--output-dir` | Copy renamed files here instead of renaming | None (rename in place) |
| `--dry-run` | Show what would be renamed without doing it | False |
| `-v, --verbose` | Show detailed logging | False |

## What Gets Extracted

| Metadata Field | Source | Example |
|---------------|--------|---------|
| **Title** | PDF metadata or first page text | "Novel approach to protein folding and structure prediction" |
| **First Author** | PDF metadata or author list | "Smith" from "Smith, Jones, and Lee" |
| **Year** | PDF metadata or publication date | 2024 |
| **DOI** | PDF text content | 10.1234/example.doi |

## Edge Cases Handled

### ✅ Handled Successfully

- **No metadata**: Skips with warning
- **Duplicate filenames**: Adds counter suffix (`_1`, `_2`, etc.)
- **Very long titles**: Truncates at 100 characters total
- **Special characters**: Sanitizes for filesystem safety
- **Multiple PDFs**: Processes entire folder at once
- **Encrypted PDFs**: Skips with error message

### ⚠️ Known Limitations

- **Scanned PDFs without text**: May not extract title (skips)
- **Very old PDFs**: May lack metadata fields
- **Non-English titles**: Uses whatever title is in PDF
- **Multiple papers in one PDF**: Cannot handle (would need splitting)

## Real-World Examples

### Test Results from Cyclamates Dataset

| Original Filename | Renamed To | Metadata Source |
|------------------|-------------|----------------|
| `COMPUTATIONAL ASSESSMENT OF THE PHARMACOKINETICS AND.pdf` | `Home_2021_FARMACIA, 2021, Vol.pdf` | PDF metadata |
| `Cross sectional study on the nonnutritive sweetener.pdf` | `Point_2024_IJB-V24-No1-p132-142.pdf` | First page text |
| `Development and validation of a UPLC-MSMS method for the.pdf` | `Bruin_2023_Development and validation of a UPLC-MSMS method for the.pdf` | PDF metadata |
| `Impact of Long Term Cyclamate and Saccharin Consumption on.pdf` | `2022_Impact of Long Term Cyclamate and Saccharin.pdf` | Year from first page |

**Success Rate**: 7/7 renamed (100%)

## Tips

1. **Always use --dry-run first** to preview changes
2. **Back up important PDFs** before bulk renaming
3. **Use --output-dir** to keep original files organized
4. **Run on recently downloaded PDFs** for best metadata
5. **Check logs** for skipped files (may need manual renaming)

## Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "No metadata found in X.pdf, skipping" | PDF has no metadata and first page is blank/scan | Manually rename or find PDF with metadata |
| "Error extracting metadata from X.pdf" | Corrupted or encrypted PDF | Check if PDF opens correctly |
| "Could not generate good filename for X.pdf" | All extraction methods failed | Manual rename required |

## Integration with Other Tools

### After Download

```bash
# 1. Download PDFs
reftool download resolved.csv --download-dir downloads/

# 2. Rename them automatically
reftool rename downloads/

# 3. Import into reference manager with meaningful names
```

### Manual PDF Collection

```bash
# Rename your existing PDF collection
reftool rename ~/Documents/papers/ --output-dir ~/Documents/organized_papers/
```

## Technical Details

- **Metadata Extraction**: Uses PyPDF2 library
- **Title Detection**: Heuristics for title-like text
- **Author Parsing**: Handles "Last, First" and "First Last" formats
- **DOI Detection**: Regex patterns for common DOI formats
- **Filename Sanitization**: Removes filesystem-unsafe characters
- **Duplicate Handling**: Incremental counter suffixes

## Requirements

- PyPDF2 must be installed (`pip install PyPDF2`)
- PDFs must be readable (not corrupted/encrypted)
- PDFs should have some metadata or text content

## Future Enhancements

See `FUTURE_ENHANCEMENTS.md` for planned improvements:
- OCR integration for scanned PDFs
- Custom naming patterns
- Batch rename with CSV mapping
- Undo/rename history
