"""Crossref API client for DOI resolution."""

import logging
import re
import time
from dataclasses import dataclass
from typing import Any

import requests

from reference_toolkit.config import Config

logger = logging.getLogger(__name__)


@dataclass
class CrossrefResult:
    """Result from a Crossref DOI lookup."""

    doi: str
    title: str
    journal: str | None = None
    year: int | None = None
    score: float = 0.0
    match_type: str = "full_citation"  # "full_citation" or "title_only"


class CrossrefClient:
    """Client for querying the Crossref API.

    API docs: https://api.crossref.org
    Etiquette: https://github.com/CrossRef/rest-api-doc#good-manners
    """

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

    def _extract_title(self, citation: str) -> str | None:
        """Extract quoted title from citation."""
        match = re.search(r'["\u201c]([^"\u201d]+)["\u201d]', citation)
        if match:
            title = match.group(1).strip()
            return title[:-1] if title.endswith(".") else title
        return None

    def _extract_first_author(self, citation: str) -> str | None:
        """Extract first author surname from citation."""
        match = re.match(r"^([A-Z][a-zA-Z\-\u2019]+)\s*,", citation)
        return match.group(1) if match else None

    def _make_request(
        self, params: dict, match_type: str
    ) -> CrossrefResult | None:
        """Make API request with retry logic.

        Args:
            params: Query parameters for the API
            match_type: "full_citation" or "title_only"

        Returns:
            CrossrefResult or None
        """
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(
                    self.BASE_URL,
                    params=params,
                    timeout=self.config.request_timeout,
                )

                # Rate limiting
                if response.status_code == 429:
                    wait = self.config.retry_backoff * (2**attempt)
                    logger.warning(f"Rate limited. Waiting {wait:.1f}s...")
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                data = response.json()
                items = data.get("message", {}).get("items", [])

                if not items:
                    return None

                item = items[0]
                result = self._parse_item(item, match_type)

                # Throttle
                time.sleep(self.config.sleep_crossref)
                return result

            except requests.Timeout:
                logger.warning(
                    f"Timeout (attempt {attempt + 1}/{self.config.max_retries})"
                )
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_backoff)

            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                break

        return None

    def _parse_item(self, item: dict, match_type: str) -> CrossrefResult:
        """Parse API response item into CrossrefResult."""
        doi = item.get("DOI", "")
        titles = item.get("title", [])
        title = titles[0] if titles else ""
        journals = item.get("container-title", [])
        journal = journals[0] if journals else None

        # Extract year
        year = None
        for field in ["published-print", "published-online", "created"]:
            if field in item:
                parts = item[field].get("date-parts", [[None]])
                if parts and parts[0]:
                    year = parts[0][0]
                    break

        score = float(item.get("score", 0))

        return CrossrefResult(
            doi=doi,
            title=title,
            journal=journal,
            year=year,
            score=score,
            match_type=match_type,
        )

    def lookup(
        self,
        citation: str,
        use_title_fallback: bool = True,
    ) -> CrossrefResult | None:
        """Resolve a citation to a DOI.

        Args:
            citation: Full citation string
            use_title_fallback: Try title-only search if full citation fails

        Returns:
            CrossrefResult or None if no match
        """
        # Primary: full bibliographic query
        params = {
            "query.bibliographic": citation,
            "rows": 1,
            "mailto": self.config.email,
        }

        result = self._make_request(params, "full_citation")
        if result:
            return result

        # Fallback: title-only search
        if use_title_fallback:
            title = self._extract_title(citation)
            if title:
                logger.info(f"Trying title fallback: {title[:50]}...")

                params = {
                    "query.title": title,
                    "rows": 1,
                    "mailto": self.config.email,
                }

                author = self._extract_first_author(citation)
                if author:
                    params["query.author"] = author

                result = self._make_request(params, "title_only")
                if result:
                    return result

        logger.warning(f"No DOI found: {citation[:60]}...")
        return None

    def get_candidates(
        self,
        citation: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Get multiple DOI candidates for manual review.

        Args:
            citation: Full citation string
            max_results: Maximum candidates to return

        Returns:
            List of dicts with title, journal, doi, score
        """
        params = {
            "query.bibliographic": citation,
            "rows": max_results,
            "mailto": self.config.email,
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()

            items = response.json().get("message", {}).get("items", [])
            candidates = []

            for item in items:
                titles = item.get("title", [])
                journals = item.get("container-title", [])
                candidates.append({
                    "title": titles[0] if titles else "",
                    "journal": journals[0] if journals else "",
                    "doi": item.get("DOI", ""),
                    "score": float(item.get("score", 0)),
                })

            time.sleep(self.config.sleep_crossref)
            return candidates

        except requests.RequestException as e:
            logger.error(f"Failed to get candidates: {e}")
            return []
