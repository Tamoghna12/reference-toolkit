"""DOI validation and correction functionality.

This module provides tools for:
- Validating DOIs directly via Crossref API
- Correcting incorrect DOIs in reference files
- Batch DOI validation with confidence scoring
- Generating discrepancy reports

Uses existing CrossrefClient infrastructure for consistency.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests

from reference_toolkit.config import Config
from reference_toolkit.crossref import CrossrefClient, CrossrefResult
from reference_toolkit.parser import ReferenceParser, ReferenceFormat

logger = logging.getLogger(__name__)


class DOIStatus(Enum):
    """Status of DOI validation."""
    VALID = "valid"
    NOT_FOUND = "not_found"
    TIMEOUT = "timeout"
    ERROR = "error"
    EXCLUDED = "excluded"


@dataclass
class DOIValidationResult:
    """Result of DOI validation."""
    doi: str
    status: DOIStatus
    title: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    score: float = 0.0
    message: str = ""
    excluded_reason: Optional[str] = None


@dataclass
class DOICorrection:
    """A DOI correction suggestion."""
    line_number: int
    citation: str
    current_doi: str
    correct_doi: str
    score: float
    title: str
    confidence_flag: str  # "high", "medium", "low"


class DOIValidator:
    """Validate and correct DOIs in reference files.

    Provides direct DOI validation without full citation resolution,
    and intelligent DOI correction with confidence scoring.

    Example:
        config = Config(email="user@example.com")
        validator = DOIValidator(config)

        # Validate single DOI
        result = validator.validate_doi("10.1038/nature12345")

        # Validate batch of DOIs
        results = validator.validate_doi_batch(["10.1038/nature12345", ...])

        # Correct DOIs in file
        corrections = validator.correct_references_file(
            input_file=Path("references.md"),
            output_file=Path("references_corrected.md")
        )
    """

    # Patterns to identify problematic DOI types
    ANNOTATION_PATTERN = re.compile(r'annotation', re.IGNORECASE)
    MASTHEAD_PATTERN = re.compile(r'masthead', re.IGNORECASE)
    PREPRINT_PATTERN = re.compile(r'10\.1101/', re.IGNORECASE)

    def __init__(self, config: Config):
        """Initialize DOI validator.

        Args:
            config: Configuration object with validation settings
        """
        self.config = config
        self.crossref = CrossrefClient(config)
        self.parser = ReferenceParser()

    def validate_doi(self, doi: str) -> DOIValidationResult:
        """Validate a single DOI via direct Crossref lookup.

        Args:
            doi: DOI string to validate

        Returns:
            DOIValidationResult with status and metadata
        """
        # Clean DOI
        doi = doi.strip().rstrip('.')

        # Check exclusions
        if self.config.get('exclude_annotation_dois', True):
            if self.ANNOTATION_PATTERN.search(doi):
                return DOIValidationResult(
                    doi=doi,
                    status=DOIStatus.EXCLUDED,
                    excluded_reason="Annotation DOI"
                )

        if self.config.get('exclude_masthead_dois', True):
            if self.MASTHEAD_PATTERN.search(doi):
                return DOIValidationResult(
                    doi=doi,
                    status=DOIStatus.EXCLUDED,
                    excluded_reason="Masthead DOI"
                )

        # Try direct API lookup
        try:
            url = f"https://api.crossref.org/works/{doi}"
            response = self.crossref.session.get(url, timeout=self.config.request_timeout)

            if response.status_code == 404:
                return DOIValidationResult(
                    doi=doi,
                    status=DOIStatus.NOT_FOUND,
                    message="DOI not found in Crossref"
                )

            response.raise_for_status()
            data = response.json()

            # Extract metadata
            item = data.get("message", {})
            title = item.get("title", [""])[0] if item.get("title") else None
            journal = item.get("container-title", [""])[0] if item.get("container-title") else None
            year = self._extract_year(item)

            return DOIValidationResult(
                doi=doi,
                status=DOIStatus.VALID,
                title=title,
                journal=journal,
                year=year,
                message="DOI resolves correctly"
            )

        except requests.Timeout:
            return DOIValidationResult(
                doi=doi,
                status=DOIStatus.TIMEOUT,
                message="Request timed out"
            )
        except requests.RequestException as e:
            return DOIValidationResult(
                doi=doi,
                status=DOIStatus.ERROR,
                message=f"Request failed: {e}"
            )
        except Exception as e:
            return DOIValidationResult(
                doi=doi,
                status=DOIStatus.ERROR,
                message=f"Unexpected error: {e}"
            )

    def validate_doi_batch(self, dois: List[str]) -> List[DOIValidationResult]:
        """Validate multiple DOIs in batch.

        Args:
            dois: List of DOI strings to validate

        Returns:
            List of DOIValidationResult objects
        """
        results = []
        total = len(dois)

        logger.info(f"Validating {total} DOIs...")

        for i, doi in enumerate(dois, 1):
            if not doi.strip():
                continue

            logger.info(f"[{i}/{total}] Checking: {doi}")
            result = self.validate_doi(doi)
            results.append(result)

            # Log status
            if result.status == DOIStatus.VALID:
                logger.info(f"  ✓ VALID - {result.title[:60] if result.title else 'N/A'}...")
            elif result.status == DOIStatus.EXCLUDED:
                logger.info(f"  ⚠ EXCLUDED ({result.excluded_reason})")
            else:
                logger.error(f"  ✗ {result.status.value.upper()}: {result.message}")

            # Rate limiting
            if i < total:
                import time
                time.sleep(self.config.sleep_crossref)

        return results

    def correct_doi_from_citation(
        self,
        citation: str,
        current_doi: str,
        confidence_threshold: float = 80.0
    ) -> Optional[DOICorrection]:
        """Find correct DOI for a citation.

        Args:
            citation: Full citation string
            current_doi: Current (possibly incorrect) DOI
            confidence_threshold: Minimum score for correction

        Returns:
            DOICorrection if correction found, None otherwise
        """
        # Lookup citation via Crossref
        result = self.crossref.lookup(citation)

        if not result:
            return None

        # Check if DOI differs
        if result.doi == current_doi:
            return None

        # Apply confidence threshold
        if result.score < confidence_threshold:
            logger.debug(f"Score {result.score:.1f} below threshold {confidence_threshold}")

        # Check exclusions
        if self.ANNOTATION_PATTERN.search(result.doi):
            return None
        if self.MASTHEAD_PATTERN.search(result.doi):
            return None

        # Determine confidence flag
        if result.score >= 90:
            confidence_flag = "high"
        elif result.score >= 70:
            confidence_flag = "medium"
        else:
            confidence_flag = "low"

        return DOICorrection(
            line_number=0,
            citation=citation[:80],
            current_doi=current_doi,
            correct_doi=result.doi,
            score=result.score,
            title=result.title,
            confidence_flag=confidence_flag
        )

    def correct_references_file(
        self,
        input_file: Path,
        output_file: Path,
        confidence_threshold: float = 80.0,
        safe_mode: bool = True
    ) -> List[DOICorrection]:
        """Correct DOIs in a reference file.

        Args:
            input_file: Input reference file (supports .txt, .bib, .ris, .md)
            output_file: Output file with corrected DOIs
            confidence_threshold: Minimum score for corrections
            safe_mode: If True, only apply high-confidence corrections

        Returns:
            List of DOICorrection objects applied
        """
        logger.info(f"Processing reference file: {input_file}")

        # Read input
        content = input_file.read_text(encoding='utf-8')
        lines = content.split('\n')

        corrections = []

        # Process each line
        for i, line in enumerate(lines):
            # Look for DOI patterns
            doi_match = re.search(r'DOI:\s*(10\.\S+)', line, re.IGNORECASE)
            if not doi_match:
                continue

            current_doi = doi_match.group(1).rstrip('.')

            # Extract citation (part before DOI)
            citation_part = re.sub(r'\.?\s*DOI:.*$', '', line, flags=re.IGNORECASE)

            # Clean citation
            citation = self._clean_citation(citation_part)

            if not citation or len(citation) < 20:
                continue

            # Try to find correct DOI
            correction = self.correct_doi_from_citation(
                citation=citation,
                current_doi=current_doi,
                confidence_threshold=confidence_threshold
            )

            if correction:
                # Apply safe mode filtering
                if safe_mode and correction.confidence_flag != "high":
                    logger.debug(f"Skipping medium/low confidence correction: {correction.current_doi}")
                    continue

                correction.line_number = i + 1
                corrections.append(correction)

                # Apply correction to line
                lines[i] = line.replace(f"DOI: {correction.current_doi}", f"DOI: {correction.correct_doi}")

                logger.info(f"Line {i+1}: {correction.current_doi} → {correction.correct_doi} (score: {correction.score:.1f})")

        # Write corrected file
        output_content = '\n'.join(lines)
        output_file.write_text(output_content, encoding='utf-8')

        logger.info(f"Applied {len(corrections)} corrections")
        logger.info(f"Output saved to: {output_file}")

        return corrections

    def generate_discrepancy_report(
        self,
        corrections: List[DOICorrection],
        output_file: Optional[Path] = None
    ) -> str:
        """Generate a detailed discrepancy report.

        Args:
            corrections: List of DOICorrection objects
            output_file: Optional file to save report

        Returns:
            Report as string
        """
        lines = []
        lines.append("=" * 100)
        lines.append("DOI CORRECTION REPORT")
        lines.append("=" * 100)
        lines.append(f"Total corrections: {len(corrections)}")

        # Group by confidence
        high_conf = [c for c in corrections if c.confidence_flag == "high"]
        med_conf = [c for c in corrections if c.confidence_flag == "medium"]
        low_conf = [c for c in corrections if c.confidence_flag == "low"]

        lines.append(f"\nConfidence breakdown:")
        lines.append(f"  High:   {len(high_conf)}")
        lines.append(f"  Medium: {len(med_conf)}")
        lines.append(f"  Low:    {len(low_conf)}")

        # Detailed corrections
        lines.append("\n" + "=" * 100)
        lines.append("DETAILED CORRECTIONS")
        lines.append("=" * 100)
        lines.append(f"{'Line':<6} {'Current DOI':<45} {'Correct DOI':<45} {'Score':<6} {'Conf':<6}")
        lines.append("=" * 100)

        for corr in corrections:
            lines.append(f"{corr.line_number:<6} {corr.current_doi:<45} {corr.correct_doi:<45} {corr.score:<6.1f} {corr.confidence_flag:<6}")

        # Manual review warnings
        if med_conf or low_conf:
            lines.append("\n" + "=" * 100)
            lines.append("⚠️  MANUAL REVIEW RECOMMENDED FOR:")
            lines.append("=" * 100)

            for corr in med_conf + low_conf:
                lines.append(f"Line {corr.line_number}: {corr.citation[:60]}...")
                lines.append(f"  Score: {corr.score:.1f} ({corr.confidence_flag} confidence)")

        report = '\n'.join(lines)

        if output_file:
            output_file.write_text(report, encoding='utf-8')
            logger.info(f"Report saved to: {output_file}")

        return report

    def _extract_year(self, item: Dict[str, Any]) -> Optional[int]:
        """Extract year from Crossref item."""
        for field in ["published-print", "published-online", "created"]:
            if field in item:
                parts = item[field].get("date-parts", [[None]])
                if parts and parts[0]:
                    return parts[0][0]
        return None

    def _clean_citation(self, citation: str) -> str:
        """Clean citation string."""
        # Remove numbering
        citation = re.sub(r'^\d+\.?\s*', '', citation)
        # Remove markdown formatting
        citation = re.sub(r'\*\*', '', citation)
        citation = re.sub(r'\*([^*]+)\*', r'\1', citation)
        # Clean quotes
        citation = citation.replace('"', '').replace('"', '')
        citation = citation.replace(''', "'").replace(''', "'")
        # Normalize whitespace
        citation = re.sub(r'\s+', ' ', citation)
        return citation.strip()
