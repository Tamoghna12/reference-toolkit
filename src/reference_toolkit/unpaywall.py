"""Unpaywall API client for open-access PDF retrieval."""

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from reference_toolkit.config import Config

logger = logging.getLogger(__name__)


@dataclass
class UnpaywallResult:
    """Result from an Unpaywall lookup."""

    doi: str
    is_oa: bool
    pdf_url: str | None = None
    oa_status: str | None = None  # gold, green, hybrid, bronze, closed
    journal: str | None = None
    publisher: str | None = None
    year: int | None = None


class UnpaywallClient:
    """Client for the Unpaywall API.

    API docs: https://unpaywall.org/products/api
    Requires email for access.
    """

    BASE_URL = "https://api.unpaywall.org/v2"

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

        # Configure proxy if specified
        if config.proxy_url:
            proxies = {"http": config.proxy_url, "https": config.proxy_url}
            self.session.proxies.update(proxies)

            # Add proxy authentication if provided
            if config.proxy_username and config.proxy_password:
                # requests handles proxy auth via URL
                from urllib.parse import urlparse
                parsed = urlparse(config.proxy_url)
                proxy_with_auth = f"{parsed.scheme}://{config.proxy_username}:{config.proxy_password}@{parsed.netloc}{parsed.path}"
                proxies = {"http": proxy_with_auth, "https": proxy_with_auth}
                self.session.proxies.update(proxies)

            logger.info(f"Using proxy: {config.proxy_url}")

    def _make_request(self, doi: str) -> dict | None:
        """Make API request with retry logic."""
        url = f"{self.BASE_URL}/{doi}"
        params = {"email": self.config.email}

        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.request_timeout,
                )

                if response.status_code == 404:
                    logger.debug(f"DOI not in Unpaywall: {doi}")
                    return None

                if response.status_code == 422:
                    logger.error(f"Invalid request (check DOI/email): {doi}")
                    return None

                if response.status_code == 429:
                    wait = self.config.retry_backoff * (2**attempt)
                    logger.warning(f"Rate limited. Waiting {wait:.1f}s...")
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                data = response.json()

                time.sleep(self.config.sleep_unpaywall)
                return data

            except requests.Timeout:
                logger.warning(
                    f"Timeout (attempt {attempt + 1}/{self.config.max_retries})"
                )
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_backoff)

            except requests.RequestException as e:
                logger.error(f"Request failed for {doi}: {e}")
                break

        return None

    def _extract_pdf_url(self, record: dict) -> str | None:
        """Find best available PDF URL from Unpaywall record.

        Priority:
        1. best_oa_location.url_for_pdf
        2. Any oa_locations[*].url_for_pdf
        3. URL that looks like PDF
        """
        # Check best location first
        best = record.get("best_oa_location") or {}
        url = best.get("url_for_pdf")
        if url:
            return url

        # Check URL field if it's a PDF
        url = best.get("url")
        if url and self._is_pdf_url(url):
            return url

        # Search all locations
        for loc in record.get("oa_locations") or []:
            url = loc.get("url_for_pdf")
            if url:
                return url

            url = loc.get("url")
            if url and self._is_pdf_url(url):
                return url

        return None

    @staticmethod
    def _is_pdf_url(url: str) -> bool:
        """Check if URL appears to point to a PDF."""
        lower = url.lower()
        return (
            ".pdf" in lower
            or "pdf" in lower.split("/")[-1]
            or "type=pdf" in lower
        )

    def lookup(self, doi: str) -> UnpaywallResult | None:
        """Look up a DOI in Unpaywall.

        Args:
            doi: DOI string

        Returns:
            UnpaywallResult or None if not found
        """
        record = self._make_request(doi)
        if not record:
            return None

        pdf_url = self._extract_pdf_url(record)

        year = None
        if record.get("published_date"):
            try:
                year = int(record["published_date"][:4])
            except (ValueError, TypeError):
                pass

        return UnpaywallResult(
            doi=doi,
            is_oa=record.get("is_oa", False),
            pdf_url=pdf_url,
            oa_status=record.get("oa_status"),
            journal=record.get("journal_name"),
            publisher=record.get("publisher"),
            year=year,
        )

    @staticmethod
    def doi_to_filename(doi: str) -> str:
        """Convert DOI to safe filename.

        Args:
            doi: DOI string

        Returns:
            Safe filename (no extension)
        """
        # Replace / with _
        safe = doi.replace("/", "_")
        # Keep only safe chars
        safe = "".join(c for c in safe if c.isalnum() or c in "._-+")
        return safe

    def download_pdf(
        self,
        url: str,
        output_path: Path | str,
    ) -> bool:
        """Download a PDF from URL.

        Args:
            url: PDF URL
            output_path: Where to save the file

        Returns:
            True if successful
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=self.config.request_timeout,
                    stream=True,
                )

                if response.status_code == 429:
                    wait = self.config.retry_backoff * (2**attempt)
                    logger.warning(f"Rate limited. Waiting {wait:.1f}s...")
                    time.sleep(wait)
                    continue

                response.raise_for_status()

                # Verify content type before downloading
                content_type = response.headers.get("Content-Type", "")
                if "pdf" not in content_type.lower() and not self._is_pdf_url(url):
                    logger.error(f"Not a PDF (Content-Type: {content_type}): {url}")
                    return False

                # Write file
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Verify file is actually a PDF
                if output_path.stat().st_size == 0:
                    logger.error("Empty file downloaded")
                    output_path.unlink()
                    return False

                # Check PDF magic bytes
                with open(output_path, "rb") as f:
                    header = f.read(4)
                    if header != b"%PDF":
                        logger.error(f"Downloaded file is not a PDF (magic bytes: {header})")
                        output_path.unlink()
                        return False

                logger.info(f"Downloaded: {output_path.name}")
                time.sleep(self.config.sleep_download)
                return True

            except requests.Timeout:
                logger.warning(
                    f"Timeout (attempt {attempt + 1}/{self.config.max_retries})"
                )
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_backoff)

            except (requests.RequestException, OSError) as e:
                logger.error(f"Download failed: {e}")
                break

        return False
