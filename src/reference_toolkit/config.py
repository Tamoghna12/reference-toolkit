"""Configuration settings for the Reference Toolkit."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class OutputFormat(Enum):
    """Supported output formats."""

    CSV = "csv"
    BIBTEX = "bibtex"
    JSON = "json"


class SearchSource(Enum):
    """Available search sources."""

    GOOGLE_SCHOLAR = "google_scholar"
    PUBMED = "pubmed"
    CROSSREF = "crossref"
    ALL = "all"


@dataclass
class Config:
    """Configuration container for the Reference Toolkit.

    All settings can be overridden via CLI arguments.
    """

    # API credentials (REQUIRED for polite API usage)
    email: str = "benzoic@gmail.com"

    # Throttling settings (seconds between API calls)
    sleep_crossref: float = 0.5
    sleep_unpaywall: float = 0.5
    sleep_download: float = 0.5
    sleep_search: float = 1.0  # Longer for web scraping

    # HTTP settings
    request_timeout: int = 30
    max_retries: int = 3
    retry_backoff: float = 10.0

    # Proxy settings (for institutional access)
    proxy_url: Optional[str] = None  # e.g., "http://proxy.institution.edu:8080"
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    use_institutional_access: bool = False

    # Preprint search settings
    search_preprints: bool = True
    search_arxiv: bool = True
    search_biorxiv: bool = True
    search_medrxiv: bool = True
    search_pmc: bool = True

    # Author contact settings
    extract_author_emails: bool = False
    author_contact_template: Optional[str] = None

    # Matching settings
    confidence_threshold: float = 60.0
    max_candidates: int = 5  # Show top N matches for review

    # Search settings
    search_limit: int = 50  # Max results per search
    search_year_start: Optional[int] = None
    search_year_end: Optional[int] = None

    # Input/output paths
    input_file: Optional[Path] = None
    output_csv: Path = field(default_factory=lambda: Path("resolved_refs.csv"))
    output_bib: Path = field(default_factory=lambda: Path("references.bib"))
    download_dir: Path = field(default_factory=lambda: Path("pdfs"))

    # Output format
    output_format: OutputFormat = OutputFormat.CSV

    # Derived paths
    @property
    def unresolved_csv(self) -> Path:
        return Path("unresolved_refs.csv")

    @property
    def low_confidence_csv(self) -> Path:
        return Path("low_confidence_refs.csv")

    @property
    def search_results_json(self) -> Path:
        return Path("search_results.json")

    @property
    def user_agent(self) -> str:
        return f"Reference-Toolkit/2.0 (mailto:{self.email})"


class Columns:
    """CSV column name constants."""

    # Input columns
    RAW_CITATION = "raw_citation"
    DOI_INPUT = "doi_input"
    PMID_INPUT = "pmid_input"
    ARXIV_INPUT = "arxiv_input"

    # Resolved metadata
    TITLE = "title"
    DOI = "doi"
    DOI_URL = "doi_url"
    AUTHORS = "authors"
    YEAR = "year"
    JOURNAL = "journal"
    VOLUME = "volume"
    ISSUE = "issue"
    PAGES = "pages"
    ISSN = "issn"
    ISBN = "isbn"
    PUBLISHER = "publisher"
    ABSTRACT = "abstract"
    KEYWORDS = "keywords"

    # Resolution metadata
    CROSSREF_SCORE = "crossref_score"
    MATCH_TYPE = "match_type"
    CONFIDENCE_FLAG = "confidence_flag"
    STATUS = "status"
    SOURCE = "source"  # Where the metadata came from

    # PDF/OA metadata
    PDF_DOWNLOADED = "pdf_downloaded"
    PDF_URL = "pdf_url"
    OA_STATUS = "oa_status"
    PDF_PATH = "pdf_path"

    # Search metadata
    CITATION_COUNT = "citation_count"
    SEARCH_RANK = "search_rank"
