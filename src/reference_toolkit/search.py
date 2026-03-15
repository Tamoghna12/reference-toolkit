"""Search module for discovering papers from multiple sources.

Supports:
- Google Scholar (via scholarly library)
- PubMed (via E-utilities API)
- Crossref (direct query)
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from xml.etree import ElementTree

import requests

from reference_toolkit.config import Config, SearchSource

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A paper found via search."""

    title: str
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    arxiv_id: Optional[str] = None
    abstract: Optional[str] = None
    citation_count: Optional[int] = None
    source: SearchSource = SearchSource.GOOGLE_SCHOLAR
    url: Optional[str] = None

    def to_citation(self) -> str:
        """Convert to standard citation format."""
        author_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            author_str += ", et al."

        citation = f'{author_str} ({self.year or "n.d."}). "{self.title}"'
        if self.journal:
            citation += f" {self.journal}"
        citation += "."
        return citation


class GoogleScholarSearch:
    """Search Google Scholar using the scholarly library."""

    def __init__(self, config: Config):
        self.config = config

    def search(
        self,
        query: str,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        limit: int = 50,
    ) -> list[SearchResult]:
        """Search Google Scholar for papers."""
        try:
            from scholarly import scholarly
        except ImportError:
            logger.error("scholarly not installed. Run: pip install scholarly")
            return []

        results = []
        try:
            search_query = scholarly.search_pubs(query)

            for i, item in enumerate(search_query):
                if i >= limit:
                    break

                # Extract year
                year = None
                if "bib" in item and "pub_year" in item["bib"]:
                    try:
                        year = int(item["bib"]["pub_year"])
                    except (ValueError, TypeError):
                        pass

                # Filter by year
                if year_start and year and year < year_start:
                    continue
                if year_end and year and year > year_end:
                    continue

                # Extract authors
                authors = []
                if "bib" in item and "author" in item["bib"]:
                    authors = item["bib"]["author"]

                result = SearchResult(
                    title=item.get("bib", {}).get("title", ""),
                    authors=authors,
                    year=year,
                    journal=item.get("bib", {}).get("venue", ""),
                    doi=self._extract_doi(item),
                    citation_count=item.get("num_citations", 0),
                    source=SearchSource.GOOGLE_SCHOLAR,
                    url=item.get("pub_url"),
                )
                results.append(result)

                time.sleep(self.config.sleep_search)

        except Exception as e:
            logger.error(f"Google Scholar search error: {e}")

        return results

    def _extract_doi(self, item: dict) -> Optional[str]:
        """Extract DOI from scholarly result."""
        # Check pub_url for DOI
        url = item.get("pub_url", "")
        if "doi.org/" in url:
            match = re.search(r"doi\.org/(10\.[^\s/]+/[^\s]+)", url)
            if match:
                return match.group(1).rstrip(".")
        return None


class PubMedSearch:
    """Search PubMed via E-utilities API."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

    def search(
        self,
        query: str,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        limit: int = 50,
    ) -> list[SearchResult]:
        """Search PubMed for papers."""
        results = []

        try:
            # Build search query
            search_query = query
            if year_start or year_end:
                year_range = f"{year_start or 1900}:{year_end or 2100}"
                search_query += f" AND {year_range}[pdat]"

            # Search for PMIDs
            search_url = f"{self.BASE_URL}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": search_query,
                "retmax": limit,
                "retmode": "json",
                "sort": "relevance",
            }

            response = self.session.get(
                search_url, params=params, timeout=self.config.request_timeout
            )
            response.raise_for_status()
            data = response.json()

            pmids = data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return []

            time.sleep(self.config.sleep_search)

            # Fetch metadata for PMIDs
            results = self._fetch_metadata(pmids)

        except Exception as e:
            logger.error(f"PubMed search error: {e}")

        return results

    def _fetch_metadata(self, pmids: list[str]) -> list[SearchResult]:
        """Fetch metadata for a list of PMIDs."""
        results = []

        fetch_url = f"{self.BASE_URL}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }

        try:
            response = self.session.get(
                fetch_url, params=params, timeout=self.config.request_timeout
            )
            response.raise_for_status()

            root = ElementTree.fromstring(response.content)

            for article in root.findall(".//PubmedArticle"):
                result = self._parse_article(article)
                if result:
                    results.append(result)

        except Exception as e:
            logger.error(f"PubMed fetch error: {e}")

        return results

    def _parse_article(self, article) -> Optional[SearchResult]:
        """Parse a PubMed article XML element."""
        try:
            medline = article.find("MedlineCitation")
            if medline is None:
                return None

            article_elem = medline.find("Article")

            # Title
            title_elem = article_elem.find("ArticleTitle")
            title = title_elem.text if title_elem is not None else ""

            # Authors
            authors = []
            author_list = article_elem.find("AuthorList")
            if author_list is not None:
                for author in author_list.findall("Author"):
                    lastname = author.find("LastName")
                    forename = author.find("ForeName")
                    if lastname is not None:
                        name = lastname.text
                        if forename is not None:
                            name += f" {forename.text}"
                        authors.append(name)

            # Year
            year = None
            journal_issue = article_elem.find("Journal/JournalIssue/PubDate/Year")
            if journal_issue is not None and journal_issue.text:
                try:
                    year = int(journal_issue.text)
                except ValueError:
                    pass

            # Journal
            journal_elem = article_elem.find("Journal/Title")
            journal = journal_elem.text if journal_elem is not None else None

            # DOI
            doi = None
            for eloc in article_elem.findall("ELocationID"):
                if eloc.get("EIdType") == "doi":
                    doi = eloc.text
                    break

            # PMID
            pmid_elem = medline.find("PMID")
            pmid = pmid_elem.text if pmid_elem is not None else None

            # Abstract
            abstract = None
            abstract_elem = article_elem.find("Abstract/AbstractText")
            if abstract_elem is not None and abstract_elem.text:
                abstract = abstract_elem.text

            return SearchResult(
                title=title,
                authors=authors,
                year=year,
                journal=journal,
                doi=doi,
                pmid=pmid,
                abstract=abstract,
                source=SearchSource.PUBMED,
            )

        except Exception as e:
            logger.debug(f"Error parsing PubMed article: {e}")
            return None


class CrossrefSearch:
    """Direct search via Crossref API."""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

    def search(
        self,
        query: str,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        limit: int = 50,
    ) -> list[SearchResult]:
        """Search Crossref for papers."""
        results = []

        try:
            url = "https://api.crossref.org/works"
            params = {
                "query": query,
                "rows": limit,
                "mailto": self.config.email,
                "sort": "relevance",
            }

            if year_start:
                params["filter"] = f"from-pub-date:{year_start}"
                if year_end:
                    params["filter"] += f",until-pub-date:{year_end}"

            response = self.session.get(
                url, params=params, timeout=self.config.request_timeout
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("message", {}).get("items", [])

            for item in items:
                result = self._parse_item(item)
                if result:
                    results.append(result)

            time.sleep(self.config.sleep_crossref)

        except Exception as e:
            logger.error(f"Crossref search error: {e}")

        return results

    def _parse_item(self, item: dict) -> Optional[SearchResult]:
        """Parse a Crossref API result."""
        try:
            title = item.get("title", [""])[0]

            authors = []
            for author in item.get("author", []):
                name = f"{author.get('family', '')} {author.get('given', '')}"
                authors.append(name.strip())

            year = None
            for field in ["published-print", "published-online", "created"]:
                if field in item:
                    parts = item[field].get("date-parts", [[None]])
                    if parts and parts[0]:
                        year = parts[0][0]
                        break

            journal = item.get("container-title", [""])[0] or None

            return SearchResult(
                title=title,
                authors=authors,
                year=year,
                journal=journal,
                doi=item.get("DOI"),
                issn=item.get("ISSN", [None])[0],
                publisher=item.get("publisher"),
                source=SearchSource.CROSSREF,
            )

        except Exception as e:
            logger.debug(f"Error parsing Crossref item: {e}")
            return None


class SearchEngine:
    """Unified search interface for all sources."""

    def __init__(self, config: Config):
        self.config = config
        self.scholar = GoogleScholarSearch(config)
        self.pubmed = PubMedSearch(config)
        self.crossref = CrossrefSearch(config)

    def search(
        self,
        query: str,
        sources: SearchSource = SearchSource.ALL,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        limit: int = 50,
    ) -> list[SearchResult]:
        """Search for papers across specified sources."""
        all_results = []

        if sources in (SearchSource.ALL, SearchSource.GOOGLE_SCHOLAR):
            logger.info(f"Searching Google Scholar: {query}")
            results = self.scholar.search(query, year_start, year_end, limit)
            all_results.extend(results)
            logger.info(f"  Found {len(results)} results")

        if sources in (SearchSource.ALL, SearchSource.PUBMED):
            logger.info(f"Searching PubMed: {query}")
            results = self.pubmed.search(query, year_start, year_end, limit)
            all_results.extend(results)
            logger.info(f"  Found {len(results)} results")

        if sources in (SearchSource.ALL, SearchSource.CROSSREF):
            logger.info(f"Searching Crossref: {query}")
            results = self.crossref.search(query, year_start, year_end, limit)
            all_results.extend(results)
            logger.info(f"  Found {len(results)} results")

        # Deduplicate by DOI
        seen_dois = set()
        unique_results = []
        for result in all_results:
            key = result.doi or result.title.lower()
            if key not in seen_dois:
                seen_dois.add(key)
                unique_results.append(result)

        return unique_results
