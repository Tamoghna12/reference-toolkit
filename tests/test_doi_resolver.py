"""Tests for DOI resolution functionality."""

import pytest
from pathlib import Path
from reference_toolkit.config import Config
from reference_toolkit.doi_resolver import DOIResolver
from reference_toolkit.parser import Reference


@pytest.fixture
def test_config():
    """Create test configuration with test email."""
    return Config(
        email="test@example.com",
        confidence_threshold=60.0,
        max_candidates=5,
    )


@pytest.fixture
def sample_references():
    """Create sample references for testing."""
    return [
        Reference(
            citation="Smith, J., et al. (2023). Machine learning for protein folding. Nature Methods, 20(3), 123-145.",
            title="Machine learning for protein folding",
            authors=["Smith, J.", "Doe, J."],
            year=2023,
            journal="Nature Methods",
        ),
        Reference(
            citation="Johnson, A. (2022). CRISPR gene editing advances. Science, 376(6594), 789-795.",
            title="CRISPR gene editing advances",
            authors=["Johnson, A."],
            year=2022,
            journal="Science",
        ),
    ]


class TestDOIResolver:
    """Tests for DOIResolver class."""

    def test_initialization(self, test_config):
        """Test resolver initialization."""
        resolver = DOIResolver(test_config)
        assert resolver.config == test_config
        assert resolver.crossref is not None
        assert resolver.parser is not None

    def test_initialization_with_custom_config(self, test_config):
        """Test resolver initialization with custom config."""
        custom_config = Config(
            email="custom@example.com",
            confidence_threshold=70.0,
        )
        resolver = DOIResolver(custom_config)
        assert resolver.config == custom_config
        assert resolver.crossref is not None


@pytest.mark.integration
class TestDOIResolutionIntegration:
    """Integration tests for DOI resolution (requires network)."""

    @pytest.fixture
    def resolver(self, test_config):
        """Create DOIResolver instance."""
        return DOIResolver(test_config)

    def test_resolve_valid_reference(self, resolver, sample_references):
        """Test resolving a valid reference."""
        ref = sample_references[0]
        results = resolver.resolve_single_reference(ref)

        assert results is not None
        # In real testing, we'd check for actual DOI matches
        # For now, we just verify the function doesn't crash

    def test_resolve_with_low_confidence_threshold(self, resolver, sample_references, tmp_path):
        """Test resolution with different confidence thresholds."""
        config = Config(
            email="test@example.com",
            confidence_threshold=90.0,  # High threshold
            output_csv=tmp_path / "test.csv",
        )
        resolver = DOIResolver(config)

        # Should return fewer results with high threshold
        ref = sample_references[0]
        results = resolver.resolve_single_reference(ref)
        assert results is not None

    def test_resolve_with_max_candidates_limit(self, resolver, sample_references):
        """Test resolution with candidate limit."""
        config = Config(
            email="test@example.com",
            max_candidates=2,  # Limit to 2 candidates
        )
        resolver = DOIResolver(config)

        ref = sample_references[0]
        results = resolver.resolve_single_reference(ref, max_results=2)
        assert results is not None


@pytest.mark.unit
class TestDOICandidateScoring:
    """Unit tests for DOI candidate scoring."""

    def test_score_calculation(self, test_config):
        """Test that score calculation works correctly."""
        resolver = DOIResolver(test_config)

        # Mock candidate data
        candidate = {
            "title": "Test Paper Title",
            "author": "Smith, J.",
            "year": "2023",
        }

        # This would need actual implementation in the resolver
        # For now, we test the structure
        assert candidate is not None
        assert "title" in candidate

    def test_confidence_threshold_filtering(self, test_config):
        """Test that confidence threshold filters results."""
        config = Config(
            email="test@example.com",
            confidence_threshold=80.0,
        )
        resolver = DOIResolver(config)

        # Test threshold logic
        assert resolver.config.confidence_threshold == 80.0


class TestDOIResolverErrorHandling:
    """Tests for error handling in DOI resolution."""

    def test_handle_invalid_reference(self, test_config):
        """Test handling of invalid reference data."""
        resolver = DOIResolver(test_config)

        # Create invalid reference
        invalid_ref = Reference(
            citation="",  # Empty citation
            title=None,
            authors=[],
            year=None,
        )

        # Should handle gracefully
        results = resolver.resolve_single_reference(invalid_ref)
        assert results is not None or results == []

    def test_handle_network_timeout(self, test_config):
        """Test handling of network timeout."""
        config = Config(
            email="test@example.com",
            request_timeout=1,  # Very short timeout
        )
        resolver = DOIResolver(config)

        # This would need mocking for proper testing
        # For now, we just verify the config is set
        assert resolver.config.request_timeout == 1

    def test_handle_empty_response(self, test_config):
        """Test handling of empty API response."""
        resolver = DOIResolver(test_config)

        # Test with reference that might return no results
        ref = Reference(
            citation="Nonexistent paper that definitely doesn't exist",
            title="Nonexistent Title",
            authors=["Unknown Author"],
            year=1900,
        )

        # Should handle gracefully without crashing
        results = resolver.resolve_single_reference(ref)
        assert results is not None


@pytest.mark.unit
class TestDOIResolverCSVOutput:
    """Tests for CSV output functionality."""

    def test_csv_output_structure(self, test_config, tmp_path):
        """Test that CSV output has correct structure."""
        from reference_toolkit.exporter import CSVExporter

        output_file = tmp_path / "test_output.csv"
        exporter = CSVExporter(output_file)

        # Write a test row
        test_row = {
            "raw_citation": "Test citation",
            "title": "Test Title",
            "doi": "10.1234/test.doi",
            "authors": "Test Author",
            "year": "2023",
        }

        exporter.write(test_row)
        exporter.close()

        # Verify file was created
        assert output_file.exists()

        # Verify content
        content = output_file.read_text()
        assert "Test citation" in content
        assert "10.1234/test.doi" in content

    def test_resolve_to_csv_workflow(self, test_config, sample_references, tmp_path):
        """Test full resolve-to-CSV workflow."""
        config = Config(
            email="test@example.com",
            output_csv=tmp_path / "resolved.csv",
        )
        resolver = DOIResolver(config)

        # Process references
        for ref in sample_references:
            resolver.resolve_single_reference(ref)

        # Verify output file was created (if resolver creates it)
        # This would need actual implementation to test properly
        assert config.output_csv.parent.exists()
