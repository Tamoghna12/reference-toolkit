"""PDF quality validation and issue detection.

This module checks downloaded PDFs for common issues:
- Corrupted files
- Encrypted/password-protected PDFs
- Scanned images (no text)
- Very small/large files
- Empty or incomplete PDFs
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logging.warning("PyPDF2 not installed. PDF quality checking will be limited.")

from reference_toolkit.config import Config

logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """Represents a PDF quality issue."""

    severity: str  # "critical", "warning", "info"
    category: str  # "corrupted", "encrypted", "scanned", "size", "empty"
    message: str
    score_penalty: int  # Points to deduct from quality score (0-100)


class PDFQualityChecker:
    """Validate PDF quality and detect issues."""

    def __init__(self, config: Config):
        self.config = config

    def check_pdf(self, pdf_path: Path) -> dict:
        """Perform comprehensive quality check on PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with keys:
                - score (int): Quality score 0-100
                - issues (list[QualityIssue]): List of issues found
                - is_valid (bool): Whether PDF is usable
                - details (dict): Additional PDF metadata
        """
        if not pdf_path.exists():
            return {
                'score': 0,
                'issues': [QualityIssue(
                    severity='critical',
                    category='missing',
                    message=f"File not found: {pdf_path}",
                    score_penalty=100
                )],
                'is_valid': False,
                'details': {}
            }

        issues: List[QualityIssue] = []
        score = 100
        details = {}

        # Check 1: File size
        size = pdf_path.stat().st_size
        details['size_bytes'] = size
        details['size_mb'] = size / (1024 * 1024)

        if size < 10_000:  # < 10KB
            issues.append(QualityIssue(
                severity='critical',
                category='size',
                message=f"Very small file ({details['size_mb']:.2f} MB - likely corrupted)",
                score_penalty=50
            ))
            score -= 50
        elif size < 50_000:  # < 50KB
            issues.append(QualityIssue(
                severity='warning',
                category='size',
                message=f"Small file ({details['size_mb']:.2f} MB - may be incomplete)",
                score_penalty=20
            ))
            score -= 20
        elif size > 100_000_000:  # > 100MB
            issues.append(QualityIssue(
                severity='info',
                category='size',
                message=f"Very large file ({details['size_mb']:.1f} MB - may be scanned images)",
                score_penalty=5
            ))
            score -= 5

        # Check 2: PDF structure (requires PyPDF2)
        if PYPDF2_AVAILABLE:
            try:
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)

                    # Check if encrypted
                    if reader.is_encrypted:
                        issues.append(QualityIssue(
                            severity='critical',
                            category='encrypted',
                            message="PDF is password-protected (cannot read)",
                            score_penalty=50
                        ))
                        score -= 50
                        return {
                            'score': max(0, score),
                            'issues': issues,
                            'is_valid': False,
                            'details': details
                        }

                    # Check page count
                    page_count = len(reader.pages)
                    details['page_count'] = page_count

                    if page_count == 0:
                        issues.append(QualityIssue(
                            severity='critical',
                            category='empty',
                            message="No pages (corrupted PDF)",
                            score_penalty=50
                        ))
                        score -= 50
                    elif page_count < 2:
                        issues.append(QualityIssue(
                            severity='warning',
                            category='incomplete',
                            message=f"Only {page_count} page(s) - may be incomplete",
                            score_penalty=20
                        ))
                        score -= 20

                    # Check for text content
                    text_content = False
                    total_text = 0
                    max_text_length = 0

                    # Sample first few pages
                    pages_to_check = min(5, page_count)
                    for i in range(pages_to_check):
                        try:
                            page = reader.pages[i]
                            text = page.extract_text()

                            if text:
                                text_len = len(text.strip())
                                total_text += text_len
                                max_text_length = max(max_text_length, text_len)

                                if text_len > 100:
                                    text_content = True
                                    break
                        except Exception as e:
                            logger.debug(f"Error reading page {i}: {e}")

                    details['has_text'] = text_content
                    details['total_text_chars'] = total_text
                    details['max_page_text'] = max_text_length

                    if not text_content:
                        issues.append(QualityIssue(
                            severity='warning',
                            category='scanned',
                            message="No selectable text (likely scanned images - OCR may be needed)",
                            score_penalty=30
                        ))
                        score -= 30
                    elif total_text < 500:
                        issues.append(QualityIssue(
                            severity='warning',
                            category='scanned',
                            message=f"Very little text ({total_text} chars) - may be partial or low-quality scan",
                            score_penalty=15
                        ))
                        score -= 15

                    # Check for common corruption signs
                    # Very short pages might indicate corruption
                    short_pages = 0
                    for i in range(min(page_count, 10)):
                        try:
                            page = reader.pages[i]
                            text = page.extract_text()
                            if text and len(text.strip()) < 50:
                                short_pages += 1
                        except Exception:
                            pass

                    if short_pages > page_count * 0.5:
                        issues.append(QualityIssue(
                            severity='warning',
                            category='corrupted',
                            message=f"Many pages appear empty or corrupted ({short_pages}/{page_count})",
                            score_penalty=25
                        ))
                        score -= 25

            except PyPDF2.errors.PyPdfError as e:
                issues.append(QualityIssue(
                    severity='critical',
                    category='corrupted',
                    message=f"Cannot read PDF structure: {e}",
                    score_penalty=50
                ))
                score -= 50
            except Exception as e:
                issues.append(QualityIssue(
                    severity='critical',
                    category='corrupted',
                    message=f"Error reading PDF: {e}",
                    score_penalty=50
                ))
                score -= 50
        else:
            # PyPDF2 not available - basic checks only
            logger.debug("PyPDF2 not available, skipping detailed checks")

        # Check 3: File extension and magic bytes
        if not pdf_path.suffix.lower() == '.pdf':
            issues.append(QualityIssue(
                severity='warning',
                category='format',
                message=f"Wrong file extension: {pdf_path.suffix}",
                score_penalty=10
            ))
            score -= 10

        # Check magic bytes
        try:
            with open(pdf_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    issues.append(QualityIssue(
                        severity='critical',
                        category='corrupted',
                        message=f"Invalid PDF header (magic bytes: {header[:4]})",
                        score_penalty=100
                    ))
                    score -= 100
        except Exception as e:
            logger.debug(f"Could not check magic bytes: {e}")

        # Determine if PDF is valid
        is_valid = score >= 60 and not any(
            i.severity == 'critical' for i in issues
        )

        return {
            'score': max(0, score),
            'issues': issues,
            'is_valid': is_valid,
            'details': details
        }

    def get_quality_summary(self, pdf_path: Path) -> str:
        """Get human-readable quality summary.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Summary string
        """
        result = self.check_pdf(pdf_path)

        status = "✓ Valid" if result['is_valid'] else "✗ Invalid"
        score_color = self._get_score_color(result['score'])

        lines = [
            f"{status} (Quality: {score_color}{result['score']}/100{'$RESET'})"
        ]

        if result['issues']:
            lines.append("Issues found:")
            for issue in result['issues']:
                lines.append(f"  - [{issue.severity.upper()}] {issue.message}")

        # Add metadata
        if result['details'].get('size_mb'):
            lines.append(f"Size: {result['details']['size_mb']:.2f} MB")
        if result['details'].get('page_count'):
            lines.append(f"Pages: {result['details']['page_count']}")

        return '\n'.join(lines)

    def _get_score_color(self, score: int) -> str:
        """Get ANSI color code for score.

        Args:
            score: Quality score

        Returns:
            ANSI color code
        """
        if score >= 80:
            return "$GREEN"  # Good
        elif score >= 60:
            return "$YELLOW"  # Acceptable
        else:
            return "$RED"  # Poor

    def validate_pdf_for_download(self, pdf_path: Path) -> bool:
        """Quick validation during download (skip detailed checks).

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF passes basic validation
        """
        if not pdf_path.exists():
            return False

        # Check magic bytes
        try:
            with open(pdf_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    logger.error(f"Invalid PDF: {pdf_path.name}")
                    return False
        except Exception:
            return False

        # Check minimum size
        size = pdf_path.stat().st_size
        if size < 10_000:  # < 10KB
            logger.warning(f"PDF too small: {pdf_path.name} ({size} bytes)")
            return False

        return True


def install_pypdf2():
    """Helper to install PyPDF2 if not available."""
    if not PYPDF2_AVAILABLE:
        logger.info("Installing PyPDF2 for PDF quality checking...")
        import subprocess
        subprocess.check_call([
            'pip', 'install', 'PyPDF2', '--quiet'
        ])
        logger.info("PyPDF2 installed successfully")
        return True
    return False
