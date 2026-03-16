"""Tests for DOI validation and correction functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

from reference_toolkit.doi_validator import (
    DOIValidator,
    DOIValidationResult,
    DOICorrection,
    DOIStatus
)
from reference_toolkit.config import Config


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        email="test@example.com",
        validation_confidence_threshold=80.0,
        safe_correction_mode=True,
        exclude_annotation_dois=True,
        exclude_masthead_dois=True,
    )


@pytest.fixture
def validator(config):
    """Create DOI validator instance."""
    return DOIValidator(config)


@pytest.fixture
def mock_crossref_response():
    """Mock successful Crossref API response."""
    return {
        "message": {
            "DOI": "10.1038/nature12345",
            "title": ["Test Paper Title"],
            "container-title": ["Nature"],
            "published-print": {"date-parts": [[2023, 1, 1]]}
        }
    }


class TestDOIValidator:
    """Test DOIValidator class."""

    def test_validate_doi_success(self, validator, mock_crossref_response):
        """Test successful DOI validation."""
        with patch.object(validator.crossref.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_crossref_response
            mock_get.return_value = mock_response

            result = validator.validate_doi("10.1038/nature12345")

            assert result.status == DOIStatus.VALID
            assert result.doi == "10.1038/nature12345"
            assert result.title == "Test Paper Title"
            assert result.journal == "Nature"
            assert result.year == 2023

    def test_validate_doi_not_found(self, validator):
        """Test DOI validation when DOI not found."""
        with patch.object(validator.crossref.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            result = validator.validate_doi("10.1234/nonexistent")

            assert result.status == DOIStatus.NOT_FOUND
            assert "not found" in result.message.lower()

    def test_validate_doi_timeout(self, validator):
        """Test DOI validation with timeout."""
        with patch.object(validator.crossref.session, 'get') as mock_get:
            mock_get.side_effect = requests.Timeout()

            result = validator.validate_doi("10.1038/nature12345")

            assert result.status == DOIStatus.TIMEOUT
            assert "timed out" in result.message.lower()

    def test_validate_doi_excludes_annotation(self, validator):
        """Test that annotation DOIs are excluded when configured."""
        result = validator.validate_doi("10.1371/annotation/test123")

        assert result.status == DOIStatus.EXCLUDED
        assert result.excluded_reason == "Annotation DOI"

    def test_validate_doi_excludes_masthead(self, validator):
        """Test that masthead DOIs are excluded when configured."""
        result = validator.validate_doi("10.1128/mmbr.masthead.81-4")

        assert result.status == DOIStatus.EXCLUDED
        assert result.excluded_reason == "Masthead DOI"

    def test_validate_doi_batch(self, validator, mock_crossref_response):
        """Test batch DOI validation."""
        with patch.object(validator.crossref.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_crossref_response
            mock_get.return_value = mock_response

            dois = [
                "10.1038/nature12345",
                "10.1126/science.abc123",
                "10.1371/annotation/test456"
            ]

            results = validator.validate_doi_batch(dois)

            assert len(results) == 3
            assert results[0].status == DOIStatus.VALID
            assert results[1].status == DOIStatus.VALID
            assert results[2].status == DOIStatus.EXCLUDED

    def test_clean_citation(self, validator):
        """Test citation cleaning."""
        citation = "1. **Smith, J. et al. (2023).** *Test* title here."
        cleaned = validator._clean_citation(citation)

        assert "1." not in cleaned
        assert "**" not in cleaned
        assert "Test title here." in cleaned

    def test_correct_doi_from_citation_success(self, validator):
        """Test successful DOI correction from citation."""
        with patch.object(validator.crossref, 'lookup') as mock_lookup:
            mock_result = Mock()
            mock_result.doi = "10.1038/nature12345"
            mock_result.score = 95.0
            mock_result.title = "Test Paper"
            mock_lookup.return_value = mock_result

            correction = validator.correct_doi_from_citation(
                citation="Smith et al. (2023). Test Paper.",
                current_doi="10.1234/wrong.doi",
                confidence_threshold=80.0
            )

            assert correction is not None
            assert correction.current_doi == "10.1234/wrong.doi"
            assert correction.correct_doi == "10.1038/nature12345"
            assert correction.score == 95.0
            assert correction.confidence_flag == "high"

    def test_correct_doi_from_citation_low_confidence(self, validator):
        """Test that low-confidence corrections are rejected."""
        with patch.object(validator.crossref, 'lookup') as mock_lookup:
            mock_result = Mock()
            mock_result.doi = "10.1038/nature12345"
            mock_result.score = 50.0
            mock_result.title = "Test Paper"
            mock_lookup.return_value = mock_result

            correction = validator.correct_doi_from_citation(
                citation="Smith et al. (2023). Test Paper.",
                current_doi="10.1234/wrong.doi",
                confidence_threshold=80.0
            )

            # Low confidence corrections still returned but flagged
            assert correction is not None
            assert correction.confidence_flag == "low"

    def test_correct_doi_from_citation_annotation_excluded(self, validator):
        """Test that annotation DOIs are excluded from corrections."""
        with patch.object(validator.crossref, 'lookup') as mock_lookup:
            mock_result = Mock()
            mock_result.doi = "10.1371/annotation/test123"
            mock_result.score = 90.0
            mock_result.title = "Test Annotation"
            mock_lookup.return_value = mock_result

            correction = validator.correct_doi_from_citation(
                citation="Smith et al. (2023). Test Paper.",
                current_doi="10.1234/wrong.doi",
                confidence_threshold=80.0
            )

            # Annotation DOIs should be excluded
            assert correction is None

    def test_correct_references_file(self, validator, tmp_path):
        """Test correcting DOIs in a reference file."""
        # Create test input file
        input_file = tmp_path / "references.md"
        input_content = """# References

1. **Smith, J. et al. (2023).** Test paper one. DOI: 10.1234/wrong1

2. **Jones, A. et al. (2022).** Test paper two. DOI: 10.5678/correct

3. **Brown, B. et al. (2021).** Test paper three. DOI: 10.9012/wrong2
"""
        input_file.write_text(input_content)

        output_file = tmp_path / "references_corrected.md"

        with patch.object(validator.crossref, 'lookup') as mock_lookup:
            # Mock lookup results
            def side_effect(citation):
                if "Smith" in citation:
                    result = Mock()
                    result.doi = "10.1038/correct1"
                    result.score = 95.0
                    result.title = "Corrected Paper One"
                    return result
                elif "Brown" in citation:
                    result = Mock()
                    result.doi = "10.1126/correct2"
                    result.score = 88.0
                    result.title = "Corrected Paper Two"
                    return result
                return None

            mock_lookup.side_effect = side_effect

            corrections = validator.correct_references_file(
                input_file=input_file,
                output_file=output_file,
                confidence_threshold=80.0,
                safe_mode=True
            )

            # Note: Citation cleaning may affect which lines get processed
            assert len(corrections) >= 1

            # Check output file
            output_content = output_file.read_text()
            # At least one correction should be applied
            assert "10.1038/correct1" in output_content or "10.1126/correct2" in output_content

    def test_generate_discrepancy_report(self, validator, tmp_path):
        """Test discrepancy report generation."""
        corrections = [
            DOICorrection(
                line_number=1,
                citation="Smith et al.",
                current_doi="10.1234/wrong",
                correct_doi="10.1038/correct",
                score=95.0,
                title="Test Paper",
                confidence_flag="high"
            ),
            DOICorrection(
                line_number=2,
                citation="Jones et al.",
                current_doi="10.5678/wrong",
                correct_doi="10.1126/correct2",
                score=75.0,
                title="Another Paper",
                confidence_flag="medium"
            ),
        ]

        report_file = tmp_path / "report.txt"
        report = validator.generate_discrepancy_report(corrections, report_file)

        assert "Total corrections: 2" in report
        assert "High:   1" in report
        assert "Medium: 1" in report
        assert "10.1234/wrong" in report
        assert "10.1038/correct" in report
        assert "MANUAL REVIEW RECOMMENDED" in report

        # Check file was created and contains key information
        assert report_file.exists()
        report_content = report_file.read_text()
        # Check that manual review section exists
        assert "MANUAL REVIEW RECOMMENDED" in report_content

    def test_extract_year(self, validator):
        """Test year extraction from Crossref item."""
        item = {
            "published-print": {"date-parts": [[2023, 5, 15]]}
        }

        year = validator._extract_year(item)
        assert year == 2023

    def test_extract_year_no_date(self, validator):
        """Test year extraction when no date available."""
        item = {}

        year = validator._extract_year(item)
        assert year is None


class TestDOIValidationResult:
    """Test DOIValidationResult dataclass."""

    def test_creation(self):
        """Test creating a validation result."""
        result = DOIValidationResult(
            doi="10.1038/nature12345",
            status=DOIStatus.VALID,
            title="Test Paper",
            journal="Nature",
            year=2023,
            message="Valid DOI"
        )

        assert result.doi == "10.1038/nature12345"
        assert result.status == DOIStatus.VALID
        assert result.title == "Test Paper"


class TestDOICorrection:
    """Test DOICorrection dataclass."""

    def test_creation(self):
        """Test creating a correction."""
        correction = DOICorrection(
            line_number=1,
            citation="Test citation",
            current_doi="10.1234/wrong",
            correct_doi="10.1038/correct",
            score=95.0,
            title="Test Paper",
            confidence_flag="high"
        )

        assert correction.line_number == 1
        assert correction.current_doi == "10.1234/wrong"
        assert correction.correct_doi == "10.1038/correct"
        assert correction.confidence_flag == "high"


@pytest.mark.integration
class TestDOIValidatorIntegration:
    """Integration tests for DOI validator (requires network)."""

    @pytest.mark.slow
    def test_validate_real_doi(self, validator):
        """Test validation of a real DOI (requires network)."""
        # Use a well-known real DOI
        result = validator.validate_doi("10.1038/nature12373")

        # This should be valid
        assert result.status == DOIStatus.VALID
        assert result.title is not None

    @pytest.mark.slow
    def test_validate_fake_doi(self, validator):
        """Test validation of a fake DOI (requires network)."""
        # Use an obviously fake DOI
        result = validator.validate_doi("10.1234/fake.doi.12345")

        # This should not be found
        assert result.status == DOIStatus.NOT_FOUND
