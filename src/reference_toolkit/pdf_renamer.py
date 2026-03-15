"""PDF batch renaming functionality.

Extracts metadata from PDF files and renames them with human-readable filenames.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

from reference_toolkit.pdf_downloader import sanitize_filename, title_to_filename

logger = logging.getLogger(__name__)


@dataclass
class PDFMetadata:
    """Metadata extracted from a PDF file."""

    path: Path
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None

    def has_metadata(self) -> bool:
        """Check if any metadata was extracted."""
        return bool(self.title or self.authors or self.year)

    def to_filename(self) -> str:
        """Generate filename from metadata."""
        return title_to_filename(
            title=self.title,
            authors=self.authors,
            year=str(self.year) if self.year else None,
            doi=self.doi,
        )


class PDFMetadataExtractor:
    """Extract metadata from PDF files."""

    def __init__(self):
        if not PYPDF2_AVAILABLE:
            raise ImportError(
                "PyPDF2 is required for PDF metadata extraction. "
                "Install it with: pip install PyPDF2"
            )

    def extract_from_pdf(self, pdf_path: Path) -> PDFMetadata:
        """Extract metadata from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            PDFMetadata object
        """
        metadata = PDFMetadata(path=pdf_path)

        if not pdf_path.exists():
            logger.warning(f"PDF not found: {pdf_path}")
            return metadata

        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)

                # Try to get metadata from PDF info
                if reader.metadata:
                    metadata.title = reader.metadata.get('/Title')
                    metadata.authors = reader.metadata.get('/Author')
                    # Extract year from metadata date if available
                    date_str = reader.metadata.get('/CreationDate')
                    if date_str:
                        year_match = re.search(r'(\d{4})', date_str)
                        if year_match:
                            metadata.year = int(year_match.group(1))

                # If no title in metadata, try extracting from first page
                if not metadata.title and len(reader.pages) > 0:
                    first_page = reader.pages[0]
                    text = first_page.extract_text()

                    # Try to extract title from first few lines
                    lines = text.strip().split('\n')[:10]
                    for line in lines:
                        line = line.strip()
                        # Skip very short lines or very long lines (likely not titles)
                        if 10 < len(line) < 200 and not line.startswith(('http', 'www', 'DOI', '©')):
                            # Check if it looks like a title (often Title Case or has capitals)
                            if any(c.isupper() for c in line[1:]):
                                metadata.title = line
                                break

                # Try to extract DOI from text
                if not metadata.doi and len(reader.pages) > 0:
                    first_page = reader.pages[0]
                    text = first_page.extract_text()
                    # Common DOI patterns
                    doi_patterns = [
                        r'\b10\.\d{4,}/[^\s]+',
                        r'\bdoi:?\s*[10]\.\d{4,}/[^\s]+',
                        r'\bDOI:\s*[10]\.\d{4,}/[^\s]+',
                    ]
                    for pattern in doi_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            metadata.doi = match.group(0).strip()
                            break

        except Exception as e:
            logger.warning(f"Error extracting metadata from {pdf_path.name}: {e}")

        return metadata

    def extract_from_folder(self, folder: Path) -> Dict[Path, PDFMetadata]:
        """Extract metadata from all PDFs in a folder.

        Args:
            folder: Path to folder containing PDFs

        Returns:
            Dictionary mapping PDF paths to their metadata
        """
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder}")

        pdf_files = list(folder.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {folder}")

        metadata_map = {}
        for pdf_path in pdf_files:
            logger.info(f"Extracting metadata from: {pdf_path.name}")
            metadata = self.extract_from_pdf(pdf_path)
            metadata_map[pdf_path] = metadata

        return metadata_map


class PDFRenamer:
    """Batch rename PDF files based on extracted metadata."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.extractor = PDFMetadataExtractor()

    def rename_pdfs(
        self,
        folder: Path,
        pattern: str = "{title}_{year}",
        output_dir: Optional[Path] = None,
    ) -> Dict[str, List[str]]:
        """Rename PDFs in folder based on their metadata.

        Args:
            folder: Path to folder containing PDFs
            pattern: Naming pattern (default: "{title}_{year}")
            output_dir: If provided, copy renamed files here instead of renaming in place

        Returns:
            Dictionary with 'renamed', 'skipped', 'failed' keys containing lists
        """
        results = {
            'renamed': [],
            'skipped': [],
            'failed': []
        }

        # Extract metadata from all PDFs
        metadata_map = self.extractor.extract_from_folder(folder)

        for old_path, metadata in metadata_map.items():
            if not metadata.has_metadata():
                logger.warning(f"No metadata found in {old_path.name}, skipping")
                results['skipped'].append(old_path.name)
                continue

            # Generate new filename
            new_filename = metadata.to_filename()

            if not new_filename or new_filename == "unknown_paper.pdf":
                logger.warning(f"Could not generate good filename for {old_path.name}")
                results['failed'].append(old_path.name)
                continue

            new_filename = new_filename + ".pdf"

            if output_dir:
                # Copy to output directory
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                new_path = output_dir / new_filename
            else:
                # Rename in place (in same folder)
                new_path = old_path.parent / new_filename

            # Handle duplicate filenames
            counter = 1
            while new_path.exists():
                base = Path(new_filename).stem
                new_filename = f"{base}_{counter}.pdf"
                if output_dir:
                    new_path = output_dir / new_filename
                else:
                    new_path = old_path.parent / new_filename
                counter += 1

            # Perform rename/copy
            try:
                if output_dir:
                    import shutil
                    shutil.copy2(old_path, new_path)
                    logger.info(f"Copied: {old_path.name} -> {new_filename}")
                else:
                    old_path.rename(new_path)
                    logger.info(f"Renamed: {old_path.name} -> {new_filename}")

                results['renamed'].append(f"{old_path.name} -> {new_filename}")

            except Exception as e:
                logger.error(f"Failed to rename {old_path.name}: {e}")
                results['failed'].append(old_path.name)

        # Summary
        logger.info("=" * 60)
        logger.info("Rename Summary")
        logger.info(f"Total PDFs: {len(metadata_map)}")
        logger.info(f"Renamed: {len(results['renamed'])}")
        logger.info(f"Skipped (no metadata): {len(results['skipped'])}")
        logger.info(f"Failed: {len(results['failed'])}")
        logger.info("=" * 60)

        return results
