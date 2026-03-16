"""Tests for reference export functionality."""

import pytest
import csv
import json
from pathlib import Path
from reference_toolkit.exporter import CSVExporter, BibTeXExporter, JSONExporter
from reference_toolkit.parser import Reference


@pytest.fixture
def sample_reference():
    """Create a sample reference for testing."""
    return Reference(
        citation="Smith, J., et al. (2023). Machine learning for protein folding. Nature Methods, 20(3), 123-145. DOI: 10.1038/s41592-023-01000-0",
        title="Machine learning for protein folding",
        authors=["Smith, J.", "Doe, J.", "Johnson, A."],
        year=2023,
        journal="Nature Methods",
        volume="20",
        issue="3",
        pages="123-145",
        doi="10.1038/s41592-023-01000-0",
        publisher="Nature Publishing Group",
        abstract="This paper presents a novel approach...",
    )


@pytest.fixture
def sample_references():
    """Create multiple sample references."""
    return [
        Reference(
            citation="Smith, J., et al. (2023). Machine learning for protein folding. Nature Methods, 20(3), 123-145.",
            title="Machine learning for protein folding",
            authors=["Smith, J.", "Doe, J."],
            year=2023,
            journal="Nature Methods",
            doi="10.1038/s41592-023-01000-0",
        ),
        Reference(
            citation="Johnson, A. (2022). CRISPR gene editing advances. Science, 376(6594), 789-795.",
            title="CRISPR gene editing advances",
            authors=["Johnson, A."],
            year=2022,
            journal="Science",
            doi="10.1126/science.abq1234",
        ),
        Reference(
            citation="Brown, R., et al. (2021). Deep learning in drug discovery. Bioorganic & Medicinal Chemistry, 29, 115987.",
            title="Deep learning in drug discovery",
            authors=["Brown, R.", "Wilson, K."],
            year=2021,
            journal="Bioorganic & Medicinal Chemistry",
        ),
    ]


class TestCSVExporter:
    """Tests for CSV export functionality."""

    def test_csv_exporter_initialization(self, tmp_path):
        """Test CSV exporter initialization."""
        exporter = CSVExporter(tmp_path / "test.csv")
        assert exporter.file is not None
        assert exporter.writer is not None

    def test_csv_export_single_reference(self, sample_reference, tmp_path):
        """Test exporting a single reference to CSV."""
        output_file = tmp_path / "test_single.csv"
        exporter = CSVExporter(output_file)

        row = CSVExporter.ref_to_row(sample_reference)
        exporter.write(row)
        exporter.close()

        # Verify file was created
        assert output_file.exists()

        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['title'] == "Machine learning for protein folding"
            assert rows[0]['doi'] == "10.1038/s41592-023-01000-0"

    def test_csv_export_multiple_references(self, sample_references, tmp_path):
        """Test exporting multiple references to CSV."""
        output_file = tmp_path / "test_multiple.csv"
        exporter = CSVExporter(output_file)

        for ref in sample_references:
            row = CSVExporter.ref_to_row(ref)
            exporter.write(row)
        exporter.close()

        # Verify all references were written
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == len(sample_references)
            assert rows[0]['title'] == "Machine learning for protein folding"
            assert rows[1]['title'] == "CRISPR gene editing advances"

    def test_ref_to_row_conversion(self, sample_reference):
        """Test conversion from Reference to CSV row."""
        row = CSVExporter.ref_to_row(sample_reference)

        assert isinstance(row, dict)
        assert 'title' in row
        assert 'authors' in row
        assert 'year' in row
        assert 'doi' in row
        assert row['title'] == "Machine learning for protein folding"
        assert row['year'] == 2023

    def test_csv_handles_missing_fields(self, tmp_path):
        """Test CSV export with missing optional fields."""
        output_file = tmp_path / "test_missing.csv"
        exporter = CSVExporter(output_file)

        # Reference with minimal fields
        minimal_ref = Reference(
            citation="Minimal citation",
            title="Minimal Title",
            authors=["Author"],
            year=2023,
        )

        row = CSVExporter.ref_to_row(minimal_ref)
        exporter.write(row)
        exporter.close()

        # Should handle missing fields gracefully
        assert output_file.exists()


class TestBibTeXExporter:
    """Tests for BibTeX export functionality."""

    def test_bibtex_exporter_initialization(self, tmp_path):
        """Test BibTeX exporter initialization."""
        exporter = BibTeXExporter(tmp_path / "test.bib")
        assert exporter.file is not None
        assert len(exporter.entries) == 0

    def test_bibtex_export_single_reference(self, sample_reference, tmp_path):
        """Test exporting a single reference to BibTeX."""
        output_file = tmp_path / "test_single.bib"
        exporter = BibTeXExporter(output_file)

        exporter.write(sample_reference)
        exporter.close()

        # Verify file was created
        assert output_file.exists()

        # Verify content contains BibTeX fields
        content = output_file.read_text()
        assert "@article" in content or "@inproceedings" in content
        assert "author" in content.lower()
        assert "title" in content.lower()
        assert "2023" in content  # year

    def test_bibtex_export_multiple_references(self, sample_references, tmp_path):
        """Test exporting multiple references to BibTeX."""
        output_file = tmp_path / "test_multiple.bib"
        exporter = BibTeXExporter(output_file)

        for ref in sample_references:
            exporter.write(ref)
        exporter.close()

        # Verify all entries were written
        content = output_file.read_text()
        # Count @article or @inproceedings entries
        entry_count = content.count("@article") + content.count("@inproceedings")
        assert entry_count == len(sample_references)

    def test_bibtex_handles_missing_doi(self, tmp_path):
        """Test BibTeX export with missing DOI."""
        output_file = tmp_path / "test_no_doi.bib"
        exporter = BibTeXExporter(output_file)

        # Reference without DOI
        ref_no_doi = Reference(
            citation="Citation without DOI",
            title="Title without DOI",
            authors=["Author"],
            year=2023,
            journal="Journal",
        )

        exporter.write(ref_no_doi)
        exporter.close()

        # Should handle missing DOI gracefully
        assert output_file.exists()
        content = output_file.read_text()
        # Should still create valid BibTeX


class TestJSONExporter:
    """Tests for JSON export functionality."""

    def test_json_exporter_initialization(self, tmp_path):
        """Test JSON exporter initialization."""
        exporter = JSONExporter(tmp_path / "test.json")
        assert exporter.data == []

    def test_json_export_single_reference(self, sample_reference, tmp_path):
        """Test exporting a single reference to JSON."""
        output_file = tmp_path / "test_single.json"
        exporter = JSONExporter(output_file)

        exporter.write(sample_reference)
        exporter.close()

        # Verify file was created
        assert output_file.exists()

        # Verify content is valid JSON
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]['title'] == "Machine learning for protein folding"

    def test_json_export_multiple_references(self, sample_references, tmp_path):
        """Test exporting multiple references to JSON."""
        output_file = tmp_path / "test_multiple.json"
        exporter = JSONExporter(output_file)

        exporter.write_all(sample_references)
        exporter.close()

        # Verify content is valid JSON with all references
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert len(data) == len(sample_references)
            assert data[0]['title'] == "Machine learning for protein folding"
            assert data[1]['title'] == "CRISPR gene editing advances"

    def test_json_output_structure(self, sample_reference, tmp_path):
        """Test that JSON output has correct structure."""
        output_file = tmp_path / "test_structure.json"
        exporter = JSONExporter(output_file)

        exporter.write(sample_reference)
        exporter.close()

        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            entry = data[0]

            # Check required fields exist
            assert 'title' in entry
            assert 'authors' in entry
            assert 'year' in entry

            # Check data types
            assert isinstance(entry['title'], str)
            assert isinstance(entry['authors'], list)
            assert isinstance(entry['year'], int)


class TestExporterErrorHandling:
    """Tests for error handling in exporters."""

    def test_csv_handles_unicode(self, tmp_path):
        """Test CSV export with Unicode characters."""
        output_file = tmp_path / "test_unicode.csv"
        exporter = CSVExporter(output_file)

        # Reference with Unicode characters
        unicode_ref = Reference(
            citation="Test with unicode café, naïve, 日本語",
            title="Test Title with Unicode: café, naïve, 日本語",
            authors=["Author", "Åuthor"],
            year=2023,
        )

        row = CSVExporter.ref_to_row(unicode_ref)
        exporter.write(row)
        exporter.close()

        # Should handle Unicode without errors
        assert output_file.exists()

    def test_bibtex_handles_special_chars(self, tmp_path):
        """Test BibTeX export with special characters."""
        output_file = tmp_path / "test_special.bib"
        exporter = BibTeXExporter(output_file)

        # Reference with special characters
        special_ref = Reference(
            citation="Test with $pecial & char{}",
            title="Title with special characters: &, %, $",
            authors=["Author"],
            year=2023,
        )

        exporter.write(special_ref)
        exporter.close()

        # Should handle special characters
        assert output_file.exists()

    def test_json_handles_nested_data(self, tmp_path):
        """Test JSON export with complex nested data."""
        output_file = tmp_path / "test_nested.json"
        exporter = JSONExporter(output_file)

        # Create reference with list fields
        complex_ref = Reference(
            citation="Complex citation",
            title="Complex Title",
            authors=["Author1", "Author2", "Author3"],
            year=2023,
        )

        exporter.write(complex_ref)
        exporter.close()

        # Verify JSON is valid
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert isinstance(data[0]['authors'], list)
            assert len(data[0]['authors']) == 3
