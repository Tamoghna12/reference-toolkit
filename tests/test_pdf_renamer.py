"""Tests for PDF metadata extraction and renaming functionality."""

import pytest
from pathlib import Path
from reference_toolkit.pdf_renamer import PDFMetadataExtractor, PDFRenamer, PDFMetadata


@pytest.fixture
def sample_metadata():
    """Create sample PDF metadata for testing."""
    return PDFMetadata(
        path=Path("test.pdf"),
        title="Test Paper Title",
        authors="Smith, J., Doe, J.",
        year=2024,
        doi="10.1234/test.doi"
    )


@pytest.fixture
def extractor():
    """Create a PDFMetadataExtractor instance."""
    return PDFMetadataExtractor()


class TestPDFMetadata:
    """Tests for PDFMetadata dataclass."""

    def test_has_metadata_with_all_fields(self, sample_metadata):
        """Test has_metadata returns True when all fields present."""
        assert sample_metadata.has_metadata() is True

    def test_has_metadata_with_partial_fields(self):
        """Test has_metadata returns True when some fields present."""
        metadata = PDFMetadata(
            path=Path("test.pdf"),
            title="Test Title"
        )
        assert metadata.has_metadata() is True

    def test_has_metadata_with_no_fields(self):
        """Test has_metadata returns False when no fields present."""
        metadata = PDFMetadata(path=Path("test.pdf"))
        assert metadata.has_metadata() is False

    def test_to_filename(self, sample_metadata):
        """Test filename generation from metadata."""
        filename = sample_metadata.to_filename()
        assert "Smith" in filename
        assert "2024" in filename
        assert "Test" in filename or "Paper" in filename


class TestPDFMetadataExtractor:
    """Tests for PDFMetadataExtractor class."""

    def test_extractor_initialization(self, extractor):
        """Test extractor initializes successfully."""
        assert extractor is not None

    def test_extract_from_nonexistent_file(self, extractor):
        """Test extraction from non-existent file returns empty metadata."""
        metadata = extractor.extract_from_pdf(Path("nonexistent.pdf"))
        assert metadata.path == Path("nonexistent.pdf")
        assert not metadata.has_metadata()

    def test_extract_from_folder_not_found(self, extractor):
        """Test extraction from non-existent folder raises error."""
        with pytest.raises(FileNotFoundError):
            extractor.extract_from_folder(Path("/nonexistent/folder"))


class TestPDFRenamer:
    """Tests for PDFRenamer class."""

    def test_renamer_initialization(self):
        """Test renamer initializes successfully."""
        renamer = PDFRenamer(dry_run=True)
        assert renamer.dry_run is True

    def test_renamer_default_dry_run(self):
        """Test renamer default dry_run is False."""
        renamer = PDFRenamer()
        assert renamer.dry_run is False


@pytest.mark.integration
class TestPDFRenamingIntegration:
    """Integration tests for PDF renaming (requires actual PDF files)."""

    def test_rename_with_sample_pdf(self, extractor, tmp_path):
        """Test renaming with actual sample PDF if available."""
        # This test requires actual PDF files in tests/fixtures/test_pdfs/
        fixture_dir = Path(__file__).parent / "fixtures" / "test_pdfs"
        if not fixture_dir.exists():
            pytest.skip("No test PDF fixtures available")

        pdf_files = list(fixture_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files in test fixtures")

        # Test extraction from first PDF
        metadata = extractor.extract_from_pdf(pdf_files[0])
        assert metadata.path == pdf_files[0]

        # If metadata found, test filename generation
        if metadata.has_metadata():
            filename = metadata.to_filename()
            assert filename != "unknown_paper.pdf"
            assert len(filename) > 0


def test_filename_sanitization():
    """Test that generated filenames are filesystem-safe."""
    metadata = PDFMetadata(
        path=Path("test.pdf"),
        title="Test: Paper with Special Characters / \\ ? * |",
        authors="O'Connor, J.",
        year=2024
    )
    filename = metadata.to_filename()
    # Should not contain problematic characters
    assert "/" not in filename
    assert "\\" not in filename
    assert "?" not in filename
    assert "*" not in filename
    assert "|" not in filename
