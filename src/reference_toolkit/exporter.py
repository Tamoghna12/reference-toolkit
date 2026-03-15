"""Export module for outputting references in various formats.

Supports:
- CSV (with full metadata)
- BibTeX (for LaTeX)
- JSON (for programmatic use)
"""

import csv
import json
import logging
from pathlib import Path
from typing import Iterable

from reference_toolkit.config import Columns, OutputFormat
from reference_toolkit.parser import Reference

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export references to CSV format."""

    # Standard column order
    COLUMNS = [
        Columns.RAW_CITATION,
        Columns.TITLE,
        Columns.DOI,
        Columns.DOI_URL,
        Columns.AUTHORS,
        Columns.YEAR,
        Columns.JOURNAL,
        Columns.VOLUME,
        Columns.ISSUE,
        Columns.PAGES,
        Columns.ISSN,
        Columns.PUBLISHER,
        Columns.CROSSREF_SCORE,
        Columns.MATCH_TYPE,
        Columns.CONFIDENCE_FLAG,
        Columns.STATUS,
        Columns.PDF_DOWNLOADED,
        Columns.PDF_URL,
        Columns.OA_STATUS,
        Columns.PDF_PATH,
    ]

    def __init__(self, path: Path):
        self.path = path
        self.file = None
        self.writer = None

    def __enter__(self):
        self.file = open(self.path, "w", encoding="utf-8", newline="")
        self.writer = csv.DictWriter(self.file, fieldnames=self.COLUMNS, extrasaction="ignore")
        self.writer.writeheader()
        return self

    def __exit__(self, *args):
        if self.file:
            self.file.close()

    def write(self, ref: dict) -> None:
        """Write a single reference row."""
        self.writer.writerow(ref)
        self.file.flush()

    def write_all(self, refs: Iterable[dict]) -> None:
        """Write all references."""
        for ref in refs:
            self.write(ref)

    @staticmethod
    def ref_to_row(ref: Reference, **extra) -> dict:
        """Convert a Reference object to a CSV row dict."""
        row = {
            Columns.RAW_CITATION: ref.citation,
            Columns.TITLE: ref.title or "",
            Columns.DOI: ref.doi or "",
            Columns.DOI_URL: f"https://doi.org/{ref.doi}" if ref.doi else "",
            Columns.AUTHORS: "; ".join(ref.authors) if ref.authors else "",
            Columns.YEAR: ref.year or "",
            Columns.JOURNAL: ref.journal or "",
            Columns.VOLUME: ref.volume or "",
            Columns.PAGES: ref.pages or "",
            Columns.ABSTRACT: ref.abstract or "",
        }
        row.update(extra)
        return row


class BibTeXExporter:
    """Export references to BibTeX format."""

    # Mapping of citation types to BibTeX entry types
    ENTRY_TYPES = {
        "article": "article",
        "journal": "article",
        "book": "book",
        "inproceedings": "inproceedings",
        "conference": "inproceedings",
        "thesis": "phdthesis",
        "phdthesis": "phdthesis",
        "mastersthesis": "mastersthesis",
        "techreport": "techreport",
        "preprint": "unpublished",
        "default": "misc",
    }

    def __init__(self, path: Path):
        self.path = path
        self.file = None

    def __enter__(self):
        self.file = open(self.path, "w", encoding="utf-8")
        return self

    def __exit__(self, *args):
        if self.file:
            self.file.close()

    def write(self, ref: Reference, entry_type: str = "article") -> None:
        """Write a single reference as BibTeX entry."""
        key = self._generate_key(ref)

        self.file.write(f"@{entry_type}{{{key},\n")

        if ref.authors:
            authors_str = " and ".join(ref.authors)
            self.file.write(f"  author = {{{self._escape(authors_str)}}},\n")

        if ref.title:
            self.file.write(f"  title = {{{{{self._escape(ref.title)}}}}},\n")

        if ref.year:
            self.file.write(f"  year = {{{ref.year}}},\n")

        if ref.journal:
            self.file.write(f"  journal = {{{self._escape(ref.journal)}}},\n")

        if ref.volume:
            self.file.write(f"  volume = {{{ref.volume}}},\n")

        if ref.issue:
            self.file.write(f"  number = {{{ref.issue}}},\n")

        if ref.pages:
            self.file.write(f"  pages = {{{ref.pages}}},\n")

        if ref.doi:
            self.file.write(f"  doi = {{{ref.doi}}},\n")

        if ref.doi:
            self.file.write(f"  url = {{https://doi.org/{ref.doi}}},\n")

        self.file.write("}\n\n")
        self.file.flush()

    def write_all(self, refs: Iterable[Reference], entry_type: str = "article") -> None:
        """Write all references."""
        for ref in refs:
            self.write(ref, entry_type)

    def _generate_key(self, ref: Reference) -> str:
        """Generate a BibTeX citation key."""
        parts = []

        # First author surname
        if ref.authors:
            surname = ref.authors[0].split()[-1].lower()
            # Remove special characters
            surname = "".join(c for c in surname if c.isalnum())
            parts.append(surname)

        # Year
        if ref.year:
            parts.append(str(ref.year))

        # First word of title
        if ref.title:
            words = ref.title.split()
            for word in words:
                if len(word) > 3 and word.isalpha():
                    parts.append(word.lower())
                    break

        return "_".join(parts) if parts else "unknown"

    @staticmethod
    def _escape(text: str) -> str:
        """Escape special characters for BibTeX."""
        replacements = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\^{}",
        }
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        return text


class JSONExporter:
    """Export references to JSON format."""

    def __init__(self, path: Path):
        self.path = path
        self.refs = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.refs, f, indent=2, ensure_ascii=False)

    def write(self, ref: Reference) -> None:
        """Add a reference to the output."""
        self.refs.append({
            "citation": ref.citation,
            "title": ref.title,
            "authors": ref.authors,
            "year": ref.year,
            "journal": ref.journal,
            "volume": ref.volume,
            "issue": ref.issue,
            "pages": ref.pages,
            "doi": ref.doi,
            "doi_url": f"https://doi.org/{ref.doi}" if ref.doi else None,
            "abstract": ref.abstract,
        })

    def write_all(self, refs: Iterable[Reference]) -> None:
        """Add all references."""
        for ref in refs:
            self.write(ref)


def get_exporter(path: Path, format: OutputFormat):
    """Get the appropriate exporter for the format."""
    if format == OutputFormat.CSV:
        return CSVExporter(path)
    elif format == OutputFormat.BIBTEX:
        return BibTeXExporter(path)
    elif format == OutputFormat.JSON:
        return JSONExporter(path)
    else:
        raise ValueError(f"Unknown format: {format}")
