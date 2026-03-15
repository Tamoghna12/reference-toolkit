"""PDF download functionality using Unpaywall."""

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from reference_toolkit.config import Config, Columns
from reference_toolkit.unpaywall import UnpaywallClient
from reference_toolkit.preprints import PreprintClient
from reference_toolkit.semantic_scholar import SemanticScholarClient
from reference_toolkit.pdf_quality import PDFQualityChecker

logger = logging.getLogger(__name__)


def sanitize_filename(text: str, max_length: int = 100) -> str:
    """Sanitize text for use as a filename.

    Args:
        text: Input text to sanitize
        max_length: Maximum filename length

    Returns:
        Safe filename string
    """
    if not text:
        return "unknown"

    # Remove or replace problematic characters
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', text)
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = text.replace('\u2013', '-').replace('\u2014', '-')  # em/en dashes
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # smart quotes
    text = text.replace('\u2018', "'").replace('\u2019', "'")

    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0]  # Break at word boundary

    return text.strip()


def title_to_filename(
    title: Optional[str] = None,
    authors: Optional[str] = None,
    year: Optional[str] = None,
    doi: Optional[str] = None,
) -> str:
    """Generate a readable filename from paper metadata.

    Format: {FirstAuthor}_{Year}_{ShortTitle}.pdf
    Falls back to DOI-based naming if metadata is unavailable.

    Args:
        title: Paper title
        authors: Author string (semicolon-separated or single name)
        year: Publication year
        doi: DOI for fallback naming

    Returns:
        Safe filename (without .pdf extension)
    """
    parts = []

    # Extract first author surname
    if authors:
        first_author = authors.split(';')[0].strip() if ';' in authors else authors
        # Handle "Last, First" or "First Last" formats
        if ',' in first_author:
            surname = first_author.split(',')[0].strip()
        else:
            surname = first_author.split()[-1].strip() if first_author.split() else ''
        if surname:
            parts.append(sanitize_filename(surname, max_length=30))

    # Add year
    if year:
        year_str = str(year).strip()
        if year_str.isdigit() and len(year_str) == 4:
            parts.append(year_str)

    # Add short title (first ~60 chars, first sentence/phrase)
    if title:
        short_title = title
        # Cut at first sentence
        for end_char in ['. ', '? ', '! ', ': ']:
            if end_char in short_title:
                short_title = short_title.split(end_char)[0]
                break
        # Remove any trailing punctuation
        short_title = short_title.rstrip('.,;:')
        parts.append(sanitize_filename(short_title, max_length=60))

    if parts:
        filename = '_'.join(parts)
        # Final cleanup
        filename = re.sub(r'_+', '_', filename)  # Collapse multiple underscores
        filename = filename.strip('_')
        if filename:
            return filename

    # Fallback to DOI-based naming
    if doi:
        return UnpaywallClient.doi_to_filename(doi)

    return "unknown_paper"


@dataclass
class DownloadResult:
    """Result from a PDF download attempt."""

    doi: str
    success: bool
    pdf_url: Optional[str] = None
    oa_status: Optional[str] = None
    error: Optional[str] = None
    output_path: Optional[Path] = None


class PDFDownloader:
    """Download open-access PDFs via Unpaywall."""

    def __init__(self, config: Config):
        self.config = config
        self.unpaywall = UnpaywallClient(config)
        self.preprints = PreprintClient(config)
        self.semantic_scholar = SemanticScholarClient(config)
        self.quality_checker = PDFQualityChecker(config)

    def _get_downloaded_dois(self) -> set[str]:
        """Get set of DOIs with existing PDFs (by checking CSV status)."""
        downloaded = set()

        # Check CSV for already downloaded DOIs
        if self.config.output_csv.exists():
            try:
                with open(self.config.output_csv, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get(Columns.PDF_DOWNLOADED) == "yes" and row.get(Columns.DOI):
                            downloaded.add(row[Columns.DOI])
            except Exception:
                pass

        return downloaded

    def download_single(
        self,
        doi: str,
        output_dir: Optional[Path] = None,
        title: Optional[str] = None,
        authors: Optional[str] = None,
        year: Optional[str] = None,
    ) -> DownloadResult:
        """Download a single PDF for a DOI.

        Args:
            doi: DOI string
            output_dir: Override output directory
            title: Paper title (for filename)
            authors: Authors string (for filename)
            year: Publication year (for filename)

        Returns:
            DownloadResult with status
        """
        output_dir = output_dir or self.config.download_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Lookup in Unpaywall
        result = self.unpaywall.lookup(doi)

        # Track PDF source
        pdf_source = "unpaywall"
        pdf_url = None
        oa_status = result.oa_status if result else None

        if result and result.is_oa and result.pdf_url:
            pdf_url = result.pdf_url
        else:
            # Try Semantic Scholar (often finds PDFs Unpaywall misses)
            if title:
                logger.info("  Not in Unpaywall, searching Semantic Scholar...")
                ss_url = self.semantic_scholar.get_pdf_url(title=title, doi=doi, authors=authors)
                if ss_url:
                    pdf_url = ss_url
                    pdf_source = "semantic_scholar"
                    logger.info(f"  ✓ Found via Semantic Scholar!")
                else:
                    # Try preprint servers if Semantic Scholar fails
                    if self.config.search_preprints:
                        logger.info("  Searching preprint servers...")
                        preprint_url = self.preprints.search_all(title, doi)
                        if preprint_url:
                            pdf_url = preprint_url
                            pdf_source = "preprint"
                            logger.info(f"  ✓ Found preprint!")

            if not pdf_url:
                return DownloadResult(
                    doi=doi,
                    success=False,
                    oa_status=oa_status,
                    error="no_oa_pdf",
                )

        if not pdf_url:
            return DownloadResult(
                doi=doi,
                success=False,
                oa_status=oa_status,
                error="no_pdf_url",
            )

        # Generate readable filename from metadata
        filename = title_to_filename(
            title=title,
            authors=authors,
            year=year,
            doi=doi,
        )
        output_path = output_dir / f"{filename}.pdf"

        # Handle duplicate filenames
        if output_path.exists():
            base = filename
            counter = 1
            while output_path.exists():
                filename = f"{base}_{counter}"
                output_path = output_dir / f"{filename}.pdf"
                counter += 1

        success = self.unpaywall.download_pdf(pdf_url, output_path)

        # Validate PDF quality after download
        if success and output_path.exists():
            quality_result = self.quality_checker.check_pdf(output_path)

            # Log quality issues
            if quality_result['issues']:
                logger.info(f"  Quality score: {quality_result['score']}/100")
                for issue in quality_result['issues'][:2]:  # Show first 2 issues
                    logger.info(f"    {issue.severity}: {issue.message}")

            # If PDF is critically bad, delete it
            if not quality_result['is_valid']:
                logger.warning(f"  PDF quality check failed, deleting: {output_path.name}")
                output_path.unlink()
                success = False
        elif not success:
            # Clean up failed downloads
            if output_path.exists():
                output_path.unlink()

        return DownloadResult(
            doi=doi,
            success=success,
            pdf_url=result.pdf_url if success else None,
            oa_status=result.oa_status,
            output_path=output_path if success else None,
            error=None if success else "download_failed",
        )

    def run(
        self,
        input_csv: Path,
        output_dir: Optional[Path] = None,
        resume: bool = False,
        update_csv: bool = True,
    ) -> dict:
        """Run the PDF download process.

        Args:
            input_csv: CSV with DOIs from resolve step
            output_dir: Directory for PDFs
            resume: Skip DOIs with existing PDFs
            update_csv: Update CSV with download status

        Returns:
            Statistics dict
        """
        stats = {
            "total_dois": 0,
            "downloaded": 0,
            "no_oa": 0,
            "failed": 0,
            "skipped": 0,
        }

        output_dir = output_dir or self.config.download_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get existing PDFs
        downloaded_dois = self._get_downloaded_dois() if resume else set()
        if downloaded_dois:
            logger.info(f"Resume: {len(downloaded_dois)} PDFs already downloaded")

        # Read CSV
        if not input_csv.exists():
            logger.error(f"Input CSV not found: {input_csv}")
            return stats

        rows = []
        with open(input_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        dois_to_process = [r for r in rows if r.get(Columns.DOI)]
        stats["total_dois"] = len(dois_to_process)

        for i, row in enumerate(dois_to_process, 1):
            doi = row[Columns.DOI]
            title = row.get(Columns.TITLE, "")
            authors = row.get(Columns.AUTHORS, "")
            year = row.get(Columns.YEAR, "")

            logger.info(f"[{i}/{len(dois_to_process)}] {title[:50] if title else doi}...")

            if resume and doi in downloaded_dois:
                logger.info("  Already downloaded, skipping")
                row[Columns.PDF_DOWNLOADED] = "yes"
                stats["skipped"] += 1
                continue

            result = self.download_single(
                doi=doi,
                output_dir=output_dir,
                title=title,
                authors=authors,
                year=year,
            )

            if result.success:
                row[Columns.PDF_DOWNLOADED] = "yes"
                row[Columns.PDF_URL] = result.pdf_url or ""
                row[Columns.OA_STATUS] = result.oa_status or ""
                row[Columns.PDF_PATH] = str(result.output_path) if result.output_path else ""
                stats["downloaded"] += 1
                logger.info(f"  ✓ Saved: {result.output_path.name if result.output_path else ''}")
            elif result.error == "no_oa_pdf":
                row[Columns.PDF_DOWNLOADED] = "no"
                row[Columns.OA_STATUS] = result.oa_status or ""
                stats["no_oa"] += 1
                logger.info(f"  No OA PDF (status: {result.oa_status})")
            else:
                row[Columns.PDF_DOWNLOADED] = "failed"
                stats["failed"] += 1
                logger.warning(f"  Download failed: {result.error}")

        # Update CSV
        if update_csv:
            self._update_csv_with_status(input_csv, rows)

        return stats

    def _update_csv_with_status(self, csv_path: Path, rows: list[dict]) -> None:
        """Update CSV with download status columns."""
        if not rows:
            return

        fieldnames = list(rows[0].keys())
        for col in [Columns.PDF_DOWNLOADED, Columns.PDF_URL, Columns.OA_STATUS, Columns.PDF_PATH]:
            if col not in fieldnames:
                fieldnames.append(col)

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                for col in fieldnames:
                    row.setdefault(col, "")
                writer.writerow(row)
