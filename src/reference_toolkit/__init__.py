"""
Reference Toolkit - Comprehensive reference management for researchers.

Features:
- Search: Google Scholar, PubMed, Crossref
- Parse: EndNote, Mendeley, BibTeX, RIS, DOI lists
- Resolve: Match citations to DOIs via Crossref
- Validate: Verify references are real and complete
- Enrich: Extract full metadata from multiple sources
- Download: Get open-access PDFs via Unpaywall
- Export: BibTeX, CSV, JSON formats
"""

__version__ = "2.0.0"

from .config import Config, Columns, OutputFormat, SearchSource
from .parser import ReferenceParser, Reference, ReferenceFormat
from .search import SearchEngine, SearchResult
from .crossref import CrossrefClient, CrossrefResult
from .unpaywall import UnpaywallClient, UnpaywallResult
from .doi_resolver import DOIResolver
from .pdf_downloader import PDFDownloader
from .exporter import BibTeXExporter, CSVExporter, JSONExporter

__all__ = [
    # Config
    "Config",
    "Columns",
    "OutputFormat",
    "SearchSource",
    # Parser
    "ReferenceParser",
    "Reference",
    "ReferenceFormat",
    # Search
    "SearchEngine",
    "SearchResult",
    # API clients
    "CrossrefClient",
    "CrossrefResult",
    "UnpaywallClient",
    "UnpaywallResult",
    # Resolver
    "DOIResolver",
    # Downloader
    "PDFDownloader",
    # Exporter
    "BibTeXExporter",
    "CSVExporter",
    "JSONExporter",
]
