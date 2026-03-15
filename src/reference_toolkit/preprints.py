"""Preprint server integration for finding OA versions of papers."""

import logging
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from functools import lru_cache
from typing import Optional
from urllib.parse import quote

import requests

from reference_toolkit.config import Config

logger = logging.getLogger(__name__)


class RateLimiter:
    """Handle rate limiting for API requests."""

    def __init__(self, requests_per_hour: int = 100):
        """Initialize rate limiter.

        Args:
            requests_per_hour: Maximum requests allowed per hour
        """
        self.requests_per_hour = requests_per_hour
        self.request_times = defaultdict(list)

    def wait_if_needed(self, domain: str):
        """Wait if rate limit would be exceeded.

        Args:
            domain: Domain being requested
        """
        now = time.time()
        hour_ago = now - 3600

        # Clean old requests
        self.request_times[domain] = [
            t for t in self.request_times[domain]
            if t > hour_ago
        ]

        # Check if we need to wait
        if len(self.request_times[domain]) >= self.requests_per_hour:
            # Calculate wait time
            oldest_request = min(self.request_times[domain])
            wait_time = 3600 - (now - oldest_request) + 1

            if wait_time > 0:
                logger.info(f"Rate limit: waiting {wait_time:.0f}s for {domain}")
                time.sleep(wait_time)

        # Record this request
        self.request_times[domain].append(now)


class PreprintClient:
    """Search for preprints of paywalled papers."""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

        # Rate limiters for different domains
        self.rate_limiters = {
            'arxiv.org': RateLimiter(requests_per_hour=100),
            'biorxiv.org': RateLimiter(requests_per_hour=100),
            'medrxiv.org': RateLimiter(requests_per_hour=100),
            'ncbi.nlm.nih.gov': RateLimiter(requests_per_hour=100),
        }

    def search_all(self, title: str, doi: Optional[str] = None) -> Optional[str]:
        """Search all preprint servers for a matching paper.

        Args:
            title: Paper title
            doi: Paper DOI (for PMC lookup)

        Returns:
            PDF URL if found, None otherwise
        """
        if not self.config.search_preprints:
            return None

        # Try arXiv
        if self.config.search_arxiv:
            self.rate_limiters['arxiv.org'].wait_if_needed('arxiv.org')
            arxiv_url = self.search_arxiv(title)
            if arxiv_url:
                logger.info(f"  ✓ Found on arXiv")
                return arxiv_url

        # Try bioRxiv
        if self.config.search_biorxiv:
            self.rate_limiters['biorxiv.org'].wait_if_needed('biorxiv.org')
            biorxiv_url = self.search_biorxiv(title)
            if biorxiv_url:
                logger.info(f"  ✓ Found on bioRxiv")
                return biorxiv_url

        # Try medRxiv
        if self.config.search_medrxiv:
            self.rate_limiters['medrxiv.org'].wait_if_needed('medrxiv.org')
            medrxiv_url = self.search_medrxiv(title)
            if medrxiv_url:
                logger.info(f"  ✓ Found on medRxiv")
                return medrxiv_url

        # Try PMC (PubMed Central)
        if self.config.search_pmc and doi:
            self.rate_limiters['ncbi.nlm.nih.gov'].wait_if_needed('ncbi.nlm.nih.gov')
            pmc_url = self.search_pmc(doi)
            if pmc_url:
                logger.info(f"  ✓ Found in PubMed Central")
                return pmc_url

        return None

    @lru_cache(maxsize=500)
    def search_arxiv(self, title: str) -> Optional[str]:
        """Search arXiv by title.

        Args:
            title: Paper title

        Returns:
            PDF URL if found
        """
        # Clean title for search
        clean_title = title.strip().lower()
        if len(clean_title) < 10:
            return None

        # Search arXiv API
        query = quote(f'ti:"{title}"')
        url = f"http://export.arxiv.org/api/query?search_query={query}&max_results=3"

        try:
            response = self.session.get(
                url,
                timeout=self.config.request_timeout,
            )

            if response.status_code == 429:
                logger.warning("arXiv rate limited, waiting...")
                time.sleep(60)  # Wait 1 minute on rate limit
                return None

            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)

            # Check for results
            entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            if entries:
                for entry in entries:
                    # Get title match
                    entry_title = entry.find('.//{http://www.w3.org/2005/Atom}title')
                    if entry_title is not None:
                        entry_title_text = entry_title.text.lower() if entry_title.text else ""

                        # Calculate similarity
                        similarity = self._title_similarity(clean_title, entry_title_text)

                        if similarity > 0.6:  # 60% similarity threshold
                            # Get PDF link
                            for link in entry.findall('.//{http://www.w3.org/2005/Atom}link'):
                                if link.get('type') == 'application/pdf':
                                    pdf_url = link.get('href')
                                    # arXiv PDF URLs need to be corrected
                                    if pdf_url.startswith('http://arxiv.org/abs/'):
                                        pdf_url = pdf_url.replace('/abs/', '/pdf/')
                                        pdf_url += '.pdf'
                                    return pdf_url

        except Exception as e:
            logger.debug(f"arXiv search failed: {e}")

        return None

    def search_biorxiv(self, title: str) -> Optional[str]:
        """Search bioRxiv by title.

        Args:
            title: Paper title

        Returns:
            PDF URL if found
        """
        # bioRxiv API: https://api.biorxiv.org/
        # Using the content API for searching

        try:
            # First, try searching by title
            search_url = "https://api.biorxiv.org/details/biorxiv"
            params = {
                'format': 'json',
            }

            # Build search query
            query = title.lower().replace(' ', '+')
            full_url = f"{search_url}/{query}"

            response = self.session.get(
                full_url,
                params=params,
                timeout=self.config.request_timeout,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('collection'):
                    paper = data['collection'][0]
                    if paper.get('pdf'):
                        return paper['pdf']

        except Exception as e:
            logger.debug(f"bioRxiv search failed: {e}")

        return None

    def search_medrxiv(self, title: str) -> Optional[str]:
        """Search medRxiv by title.

        Args:
            title: Paper title

        Returns:
            PDF URL if found
        """
        # medRxiv uses similar API to bioRxiv
        try:
            search_url = "https://api.medrxiv.org/details/medrxiv"
            query = title.lower().replace(' ', '+')
            full_url = f"{search_url}/{query}"

            response = self.session.get(
                full_url,
                params={'format': 'json'},
                timeout=self.config.request_timeout,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('collection'):
                    paper = data['collection'][0]
                    if paper.get('pdf'):
                        return paper['pdf']

        except Exception as e:
            logger.debug(f"medRxiv search failed: {e}")

        return None

    def search_pmc(self, doi: str) -> Optional[str]:
        """Search PubMed Central by DOI.

        Args:
            doi: Paper DOI

        Returns:
            PDF URL if found in PMC
        """
        # PMC ID Converter API
        url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/id/ai/v1/{doi}"

        try:
            response = self.session.get(url, timeout=self.config.request_timeout)

            if response.status_code == 404:
                return None

            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)

            # Look for PMCID
            for record in root.findall('.//{http://www.ncbi.nlm.nih.gov/2008/elements/v1/}record'):
                pmcid = record.get('pmcid')
                if pmcid:
                    # Return PDF URL
                    return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"

        except Exception as e:
            logger.debug(f"PMC search failed: {e}")

        return None

    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles.

        Args:
            title1: First title
            title2: Second title

        Returns:
            Similarity score (0-1)
        """
        # Normalize titles
        words1 = set(title1.split())
        words2 = set(title2.split())

        if not words1 or not words2:
            return 0.0

        # Calculate word overlap
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0
