"""Semantic Scholar API client for enhanced paper discovery.

Semantic Scholar is a free, AI-powered research tool that:
- Indexes 200M+ papers across all fields
- Provides open access PDF links
- Offers citation counts and influence metrics
- Has a generous free API

API docs: https://api.semanticscholar.org/api-docs/
"""

import logging
from typing import Optional
from urllib.parse import quote

import requests

from reference_toolkit.config import Config

logger = logging.getLogger(__name__)


class SemanticScholarClient:
    """Client for Semantic Scholar API.

    Semantic Scholar often finds OA PDFs that Unpaywall misses,
    especially from:
    - University repositories
    - Preprint servers
    - Author websites
    - ResearchGate profiles
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.user_agent,
            "Accept": "application/json"
        })

        # Semantic Scholar API key (optional but recommended for higher limits)
        self.api_key = getattr(config, 'semantic_scholar_key', None)

    def search_paper(
        self,
        title: str = "",
        doi: str = "",
        authors: str = ""
    ) -> Optional[dict]:
        """Search for paper metadata and OA PDF link.

        Args:
            title: Paper title (for fallback search)
            doi: Paper DOI (preferred method)
            authors: Author string (for better matching)

        Returns:
            Paper data dict with keys:
                - paperId (str)
                - title (str)
                - authors (list)
                - year (int)
                - openAccessPdf (dict with url field)
                - citationCount (int)
                - influentialCitationCount (int)
        """
        # Try DOI first (most accurate)
        if doi:
            result = self._get_by_doi(doi)
            if result and result.get('openAccessPdf'):
                return result

        # Fallback to title search
        if title:
            result = self._search_by_title(title, authors)
            if result and result.get('openAccessPdf'):
                return result

        return None

    def _get_by_doi(self, doi: str) -> Optional[dict]:
        """Get paper by DOI from Semantic Scholar.

        Args:
            doi: Paper DOI

        Returns:
            Paper data dict or None
        """
        # Remove common DOI prefixes if present
        clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')

        url = f"{self.BASE_URL}/paper/DOI:{clean_doi}"
        params = {
            'fields': 'paperId,title,authors,year,openAccessPdf,citationCount,influentialCitationCount,externalIds'
        }

        if self.api_key:
            params['api_key'] = self.api_key

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.request_timeout
            )

            if response.status_code == 404:
                logger.debug(f"Not in Semantic Scholar: {doi}")
                return None

            if response.status_code == 429:
                logger.warning("Semantic Scholar rate limited")
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.debug(f"Semantic Scholar DOI lookup failed: {e}")
            return None

    def _search_by_title(self, title: str, authors: str = "") -> Optional[dict]:
        """Search by paper title (fallback method).

        Args:
            title: Paper title
            authors: Author string for better matching

        Returns:
            Paper data dict or None
        """
        url = f"{self.BASE_URL}/paper/search"
        params = {
            'query': title,
            'limit': 5,
            'fields': 'paperId,title,authors,year,openAccessPdf,citationCount'
        }

        if self.api_key:
            params['api_key'] = self.api_key

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.request_timeout
            )

            if response.status_code == 429:
                logger.warning("Semantic Scholar rate limited")
                return None

            response.raise_for_status()
            data = response.json()

            # Check results
            results = data.get('data', [])
            if not results:
                return None

            # Find best match using title similarity
            best_match = None
            best_score = 0.0

            for paper in results:
                score = self._calculate_similarity(title, paper.get('title', ''))

                # Bonus if authors match
                if authors and paper.get('authors'):
                    if self._authors_match(authors, paper['authors']):
                        score += 0.2

                if score > best_score:
                    best_score = score
                    best_match = paper

            # Return if similarity is high enough
            if best_score > 0.6:
                return best_match

        except Exception as e:
            logger.debug(f"Semantic Scholar title search failed: {e}")

        return None

    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles.

        Args:
            title1: First title
            title2: Second title

        Returns:
            Similarity score (0-1)
        """
        if not title1 or not title2:
            return 0.0

        # Normalize
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()

        # Exact match
        if t1 == t2:
            return 1.0

        # Word overlap
        words1 = set(t1.split())
        words2 = set(t2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _authors_match(self, authors_str: str, ss_authors: list) -> bool:
        """Check if author lists match.

        Args:
            authors_str: Semicolon-separated author string
            ss_authors: Semantic Scholar author list

        Returns:
            True if first author matches
        """
        if not authors_str or not ss_authors:
            return False

        # Get first author from our list
        first_author = authors_str.split(';')[0].strip()

        # Normalize
        first_author = first_author.lower()

        # Check against SS authors
        for author in ss_authors[:3]:  # Check first 3 authors
            ss_name = author.get('name', '').lower()
            if ss_name:
                # Handle "Last, First" format
                if ',' in first_author:
                    last_name = first_author.split(',')[0].strip()
                else:
                    last_name = first_author.split()[-1].strip()

                if last_name in ss_name or ss_name in first_author:
                    return True

        return False

    def get_pdf_url(self, title: str = "", doi: str = "", authors: str = "") -> Optional[str]:
        """Get direct PDF URL from Semantic Scholar.

        Args:
            title: Paper title
            doi: Paper DOI
            authors: Author string

        Returns:
            PDF URL if found, None otherwise
        """
        paper = self.search_paper(title=title, doi=doi, authors=authors)

        if paper and paper.get('openAccessPdf'):
            pdf_url = paper['openAccessPdf'].get('url')
            if pdf_url:
                logger.info(f"  ✓ Found via Semantic Scholar")
                logger.debug(f"    Citation count: {paper.get('citationCount', 0)}")
                return pdf_url

        return None
