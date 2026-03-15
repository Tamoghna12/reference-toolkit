"""Reference parsing module for EndNote, Mendeley, and other reference managers.

Supports:
- EndNote plain text exports
- Mendeley plain text exports
- BibTeX files (.bib)
- RIS files (.ris)
- Generic reference lists
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional


class ReferenceFormat(Enum):
    """Supported reference formats."""

    ENDNOTE = "endnote"
    MENDELEY = "mendeley"
    BIBTEX = "bibtex"
    RIS = "ris"
    AUTO = "auto"


@dataclass
class Reference:
    """A parsed reference with citation and optional metadata."""

    citation: str
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    line_number: int = 0
    doi: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    source_format: ReferenceFormat = ReferenceFormat.ENDNOTE


class EndNoteParser:
    """Parse EndNote plain text exports.

    Format: "Author, I., et al. (Year). "Title." Journal Vol: Pages."
    """

    HEADER_PATTERN = re.compile(
        r"^"
        r"(?:"
        r"[A-Z][a-zA-Z\-\u2019]+"
        r",\s*"
        r"(?:[A-Z]\.(?:\s*[A-Z]\.)*)"
        r"(?:,?\s*(?:et\s+al\.?|and\s+[A-Z][a-z]+))?"
        r"\.\s*"
        r")?"
        r"\("
        r"(?:19|20)\d{2}"
        r"[a-z]?"
        r"\)"
        r"\.\s*"
        r'["\u201c]'
    )

    @classmethod
    def is_header(cls, line: str) -> bool:
        if not line.strip():
            return False
        if cls.HEADER_PATTERN.match(line.strip()):
            return True
        # Fallback
        has_year = bool(re.search(r"\((?:19|20)\d{2}[a-z]?\)", line))
        has_quote = '"' in line or "\u201c" in line
        return has_year and has_quote


class MendeleyParser:
    """Parse Mendeley plain text exports.

    Mendeley exports are similar to EndNote but may have:
    - Different author formatting (First Last instead of Last, First)
    - Different separator patterns
    - DOI included on separate line
    """

    # Mendeley-style header (more flexible than EndNote)
    HEADER_PATTERN = re.compile(
        r"^"
        r"(?:"
        r"[A-Z][a-zA-Z\-\u2019\s]+"  # Author names
        r"(?:,?\s*(?:et\s+al\.?|and\s+[A-Z][a-z]+))?"
        r"(?:\.\s*|\s+)"  # Period or space
        r")?"
        r"\("
        r"(?:19|20)\d{2}"
        r"[a-z]?"
        r"\)"
        r"\.?\s*"
        r'["\u201c]'
    )

    # DOI pattern
    DOI_PATTERN = re.compile(r"^doi:\s*(10\.\d{4,}/[^\s]+)", re.IGNORECASE)
    DOI_URL_PATTERN = re.compile(r"https?://(?:dx\.)?doi\.org/(10\.[^\s]+)", re.IGNORECASE)

    @classmethod
    def is_header(cls, line: str) -> bool:
        if not line.strip():
            return False
        if cls.HEADER_PATTERN.match(line.strip()):
            return True
        # Fallback: year + title in quotes
        has_year = bool(re.search(r"\((?:19|20)\d{2}[a-z]?\)", line))
        has_quote = '"' in line or "\u201c" in line
        return has_year and has_quote

    @classmethod
    def extract_doi(cls, line: str) -> Optional[str]:
        """Extract DOI from a line if present."""
        match = cls.DOI_PATTERN.match(line.strip())
        if match:
            return match.group(1).rstrip(".")
        match = cls.DOI_URL_PATTERN.search(line)
        if match:
            return match.group(1).rstrip(".")
        return None


class BibTeXParser:
    """Parse BibTeX files (.bib)."""

    ENTRY_PATTERN = re.compile(r"^@\w+\{[^,]+,")
    FIELD_PATTERN = re.compile(r"(\w+)\s*=\s*[{\"'](.+?)[}\"']", re.DOTALL)

    @classmethod
    def is_bibtex(cls, content: str) -> bool:
        """Check if content looks like BibTeX."""
        return bool(cls.ENTRY_PATTERN.search(content))

    @classmethod
    def parse_entries(cls, content: str) -> Iterator[dict]:
        """Parse BibTeX entries into dicts."""
        # Split into entries
        entry_starts = [
            m.start() for m in re.finditer(r"@\w+\{([^,]+),", content)
        ]

        for i, start in enumerate(entry_starts):
            end = entry_starts[i + 1] if i + 1 < len(entry_starts) else len(content)
            entry_text = content[start:end]

            # Extract entry type and key
            header_match = re.match(r"@(\w+)\{([^,]+),", entry_text)
            if not header_match:
                continue

            entry = {
                "type": header_match.group(1).lower(),
                "key": header_match.group(2),
            }

            # Extract fields
            for match in re.finditer(r"(\w+)\s*=\s*[{\"'](.+?)[}\"']\s*,?", entry_text, re.DOTALL):
                field_name = match.group(1).lower()
                field_value = match.group(2).strip()
                # Clean up the value
                field_value = re.sub(r"\s+", " ", field_value)
                entry[field_name] = field_value

            yield entry


class RISParser:
    """Parse RIS files (.ris)."""

    TAG_PATTERN = re.compile(r"^([A-Z0-9]{2})\s*[-–]\s*(.*)$")

    @classmethod
    def is_ris(cls, content: str) -> bool:
        """Check if content looks like RIS."""
        return bool(re.search(r"^(TY|ER)\s*[-–]", content, re.MULTILINE))

    @classmethod
    def parse_entries(cls, content: str) -> Iterator[dict]:
        """Parse RIS entries into dicts."""
        entry = {}

        for line in content.split("\n"):
            match = cls.TAG_PATTERN.match(line.strip())
            if match:
                tag, value = match.groups()
                value = value.strip()

                if tag == "ER":
                    if entry:
                        yield entry
                    entry = {}
                elif tag in entry:
                    # Multi-value field
                    if isinstance(entry[tag], list):
                        entry[tag].append(value)
                    else:
                        entry[tag] = [entry[tag], value]
                else:
                    entry[tag] = value

        if entry:
            yield entry


class ReferenceParser:
    """Unified parser for reference files from various sources.

    Auto-detects format or uses specified format.

    Usage:
        parser = ReferenceParser()
        refs = parser.parse_file("references.txt")
        refs = parser.parse_file("references.bib", format=ReferenceFormat.BIBTEX)
    """

    def __init__(self, format: ReferenceFormat = ReferenceFormat.AUTO):
        self.format = format

    def detect_format(self, path: Path) -> ReferenceFormat:
        """Auto-detect the file format."""
        suffix = path.suffix.lower()

        if suffix == ".bib":
            return ReferenceFormat.BIBTEX
        if suffix == ".ris":
            return ReferenceFormat.RIS

        # Check content
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")

            if BibTeXParser.is_bibtex(content):
                return ReferenceFormat.BIBTEX
            if RISParser.is_ris(content):
                return ReferenceFormat.RIS

            # Default to EndNote/Mendeley style
            return ReferenceFormat.ENDNOTE

        except Exception:
            return ReferenceFormat.ENDNOTE

    def parse_file(
        self, path: Path | str, format: ReferenceFormat | None = None
    ) -> list[Reference]:
        """Parse all references from a file."""
        return list(self.iter_references(Path(path), format))

    def iter_references(
        self, path: Path, format: ReferenceFormat | None = None
    ) -> Iterator[Reference]:
        """Iterate over references in a file."""

        fmt = format or self.format
        if fmt == ReferenceFormat.AUTO:
            fmt = self.detect_format(path)

        if fmt == ReferenceFormat.BIBTEX:
            yield from self._parse_bibtex(path)
        elif fmt == ReferenceFormat.RIS:
            yield from self._parse_ris(path)
        else:
            yield from self._parse_text(path, fmt)

    def _parse_text(self, path: Path, fmt: ReferenceFormat) -> Iterator[Reference]:
        """Parse plain text reference files (EndNote/Mendeley)."""

        current_ref: Reference | None = None
        abstract_lines: list[str] = []
        line_num = 0

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line_num += 1
                stripped = line.strip()

                if not stripped:
                    continue

                # Check for DOI line (Mendeley)
                doi = MendeleyParser.extract_doi(stripped)
                if doi and current_ref:
                    current_ref.doi = doi
                    continue

                # Check if this is a header line
                is_header = (
                    EndNoteParser.is_header(stripped)
                    or MendeleyParser.is_header(stripped)
                )

                if is_header:
                    # Yield previous reference
                    if current_ref:
                        current_ref.abstract = " ".join(abstract_lines)
                        yield current_ref

                    # Start new reference
                    current_ref = Reference(
                        citation=self.clean_citation(stripped),
                        line_number=line_num,
                        source_format=fmt,
                    )
                    abstract_lines = []

                elif current_ref:
                    abstract_lines.append(stripped)

        # Yield final reference
        if current_ref:
            current_ref.abstract = " ".join(abstract_lines)
            yield current_ref

    def _parse_bibtex(self, path: Path) -> Iterator[Reference]:
        """Parse BibTeX file."""

        content = path.read_text(encoding="utf-8")

        for i, entry in enumerate(BibTeXParser.parse_entries(content), 1):
            # Build citation string from fields
            authors = entry.get("author", "")
            title = entry.get("title", "")
            year = entry.get("year", "")
            journal = entry.get("journal", entry.get("booktitle", ""))
            volume = entry.get("volume", "")
            pages = entry.get("pages", "")
            doi = entry.get("doi", "")

            # Format as standard citation
            citation = f'{authors} ({year}). "{title}"'
            if journal:
                citation += f" {journal}"
            if volume:
                citation += f" {volume}"
            if pages:
                citation += f": {pages}"
            citation += "."

            yield Reference(
                citation=citation,
                abstract=entry.get("abstract", ""),
                line_number=i,
                doi=doi if doi else None,
                title=title,
                authors=[a.strip() for a in authors.split(" and ")],
                year=int(year) if year.isdigit() else None,
                journal=journal,
                source_format=ReferenceFormat.BIBTEX,
            )

    def _parse_ris(self, path: Path) -> Iterator[Reference]:
        """Parse RIS file."""

        content = path.read_text(encoding="utf-8")

        for i, entry in enumerate(RISParser.parse_entries(content), 1):
            # Build citation from RIS fields
            # AU = author, TI = title, PY = year, JO/T2 = journal
            authors = entry.get("AU", [])
            if isinstance(authors, str):
                authors = [authors]

            title = entry.get("TI", entry.get("T1", ""))
            year = entry.get("PY", "")
            journal = entry.get("JO", entry.get("T2", ""))
            volume = entry.get("VL", "")
            pages = entry.get("SP", "")
            doi = entry.get("DO", "")

            # Format citation
            author_str = ", ".join(authors) if authors else "Unknown"
            citation = f'{author_str} ({year}). "{title}"'
            if journal:
                citation += f" {journal}"
            if volume:
                citation += f" {volume}"
            if pages:
                citation += f": {pages}"
            citation += "."

            yield Reference(
                citation=citation,
                abstract=entry.get("AB", ""),
                line_number=i,
                doi=doi if doi else None,
                title=title,
                authors=authors,
                year=int(year[:4]) if year and year[:4].isdigit() else None,
                journal=journal,
                source_format=ReferenceFormat.RIS,
            )

    @staticmethod
    def clean_citation(citation: str) -> str:
        """Normalize a citation string."""
        text = citation
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def extract_title(citation: str) -> str | None:
        """Extract quoted title from citation."""
        match = re.search(r'["\u201c]([^"\u201d]+)["\u201d]', citation)
        if match:
            title = match.group(1).strip()
            return title[:-1] if title.endswith(".") else title
        return None

    @staticmethod
    def extract_first_author(citation: str) -> str | None:
        """Extract first author surname."""
        match = re.match(r"^([A-Z][a-zA-Z\-\u2019]+)\s*,", citation)
        return match.group(1) if match else None

    def parse_citations_only(self, path: Path | str) -> list[str]:
        """Parse only citation strings (skip metadata)."""
        return [ref.citation for ref in self.iter_references(Path(path))]
