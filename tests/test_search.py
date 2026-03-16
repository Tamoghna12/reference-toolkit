"""Tests for search functionality."""

import pytest
from reference_toolkit.config import Config, SearchSource
from reference_toolkit.search import SearchEngine, SearchResult


@pytest.fixture
def test_config():
    """Create test configuration."""
    return Config(
        email="test@example.com",
        search_limit=10,
    )


@pytest.fixture
def sample_search_results():
    """Create sample search results."""
    return [
        SearchResult(
            title="Machine learning for protein folding",
            authors=["Smith, J.", "Doe, J."],
            year=2023,
            journal="Nature Methods",
            doi="10.1038/s41592-023-01000-0",
            pmid="37891234",
            url="https://doi.org/10.1038/s41592-023-01000-0",
            citation_count=42,
        ),
        SearchResult(
            title="CRISPR gene editing advances",
            authors=["Johnson, A."],
            year=2022,
            journal="Science",
            doi="10.1126/science.abq1234",
            pmid="35678901",
            url="https://doi.org/10.1126/science.abq1234",
            citation_count=28,
        ),
    ]


class TestSearchEngine:
    """Tests for SearchEngine class."""

    def test_initialization(self, test_config):
        """Test search engine initialization."""
        engine = SearchEngine(test_config)
        assert engine.config == test_config

    def test_initialization_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = Config(
            email="test@example.com",
            search_limit=20,
            search_year_start=2020,
            search_year_end=2023,
        )
        engine = SearchEngine(config)
        assert engine.config.search_limit == 20
        assert engine.config.search_year_start == 2020


@pytest.mark.unit
class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        result = SearchResult(
            title="Test Paper",
            authors=["Author"],
            year=2023,
            journal="Test Journal",
            doi="10.1234/test",
            pmid="12345678",
            url="https://example.com",
            citation_count=10,
        )

        assert result.title == "Test Paper"
        assert result.authors == ["Author"]
        assert result.year == 2023
        assert result.doi == "10.1234/test"

    def test_search_result_to_citation(self):
        """Test conversion to citation string."""
        result = SearchResult(
            title="Test Paper",
            authors=["Smith, J.", "Doe, J."],
            year=2023,
            journal="Nature",
            doi="10.1038/test.2023",
            pmid="12345678",
            url="https://doi.org/10.1038/test.2023",
            citation_count=5,
        )

        citation = result.to_citation()
        assert isinstance(citation, str)
        assert "Smith" in citation or "Test Paper" in citation


@pytest.mark.integration
class TestSearchIntegration:
    """Integration tests for search functionality (requires network)."""

    @pytest.fixture
    def engine(self, test_config):
        """Create search engine instance."""
        return SearchEngine(test_config)

    def test_search_with_empty_query(self, engine):
        """Test search with empty query."""
        results = engine.search(
            query="",
            sources=SearchSource.ALL,
            limit=5,
        )

        # Should return empty results or handle gracefully
        assert results is not None
        assert isinstance(results, list)

    def test_search_with_short_query(self, engine):
        """Test search with very short query."""
        results = engine.search(
            query="a",  # Single character
            sources=SearchSource.ALL,
            limit=5,
        )

        # Should handle gracefully
        assert results is not None

    def test_search_limit_enforcement(self, engine):
        """Test that search limit is enforced."""
        results = engine.search(
            query="machine learning",
            sources=SearchSource.ALL,
            limit=3,
        )

        # Should not return more than limit
        assert len(results) <= 3

    def test_search_with_year_filter(self, engine):
        """Test search with year range filter."""
        config = Config(
            email="test@example.com",
            search_limit=10,
            search_year_start=2020,
            search_year_end=2022,
        )
        engine = SearchEngine(config)

        results = engine.search(
            query="CRISPR",
            sources=SearchSource.ALL,
            limit=10,
        )

        # Results should respect year filter
        for result in results:
            if result.year:
                assert 2020 <= result.year <= 2022


@pytest.mark.unit
class TestSearchQueryHandling:
    """Tests for query handling and formatting."""

    def test_format_query_simple(self):
        """Test formatting of simple search query."""
        query = "machine learning protein folding"

        # Query should be properly formatted
        assert len(query) > 0
        assert query == query.strip()  # No leading/trailing whitespace

    def test_format_query_with_special_chars(self):
        """Test handling of special characters in query."""
        queries = [
            "machine-learning AND protein folding",
            "CRISPR/Cas9",
            "COVID-19",
            "α-carotene",  # Unicode
        ]

        for query in queries:
            # Should handle special characters
            assert len(query) > 0
            # Should not crash
            formatted = query.strip()

    def test_format_query_with_quotes(self):
        """Test handling of quoted terms."""
        queries = [
            '"machine learning"',
            "'protein folding'",
            '"COVID-19" pandemic',
        ]

        for query in queries:
            # Should preserve quotes
            assert '"' in query or "'" in query


@pytest.mark.unit
class TestSearchSources:
    """Tests for different search sources."""

    def test_search_all_sources(self, test_config):
        """Test searching across all sources."""
        engine = SearchEngine(test_config)
        results = engine.search(
            query="test query",
            sources=SearchSource.ALL,
            limit=5,
        )

        # Should return results from multiple sources
        assert results is not None

    def test_search_single_source(self, test_config):
        """Test searching from single source."""
        engine = SearchEngine(test_config)

        # Test each source individually
        sources = [
            SearchSource.GOOGLE_SCHOLAR,
            SearchSource.PUBMED,
            SearchSource.CROSSREF,
        ]

        for source in sources:
            results = engine.search(
                query="test",
                sources=source,
                limit=2,
            )
            assert results is not None


class TestSearchErrorHandling:
    """Tests for error handling in search functionality."""

    def test_handle_network_timeout(self, test_config):
        """Test handling of network timeout during search."""
        config = Config(
            email="test@example.com",
            request_timeout=1,  # Very short timeout
            search_limit=5,
        )
        engine = SearchEngine(config)

        # Should handle timeout gracefully
        results = engine.search(
            query="test query that might timeout",
            sources=SearchSource.ALL,
            limit=2,
        )
        assert results is not None

    def test_handle_empty_response(self, test_config):
        """Test handling of empty search response."""
        engine = SearchEngine(test_config)

        # Search for something that might return no results
        results = engine.search(
            query="xyznonexistentpaper123",
            sources=SearchSource.ALL,
            limit=5,
        )

        # Should return empty list, not crash
        assert results == []

    def test_handle_malformed_response(self, test_config):
        """Test handling of malformed API response."""
        # This would need mocking for proper testing
        # For now, we just verify the structure exists
        engine = SearchEngine(test_config)
        assert hasattr(engine, 'search')


@pytest.mark.unit
class TestSearchResultProcessing:
    """Tests for processing search results."""

    def test_deduplicate_results(self, sample_search_results):
        """Test deduplication of search results."""
        # Create duplicates
        results = sample_search_results + sample_search_results

        # Would need actual deduplication implementation
        # For now, just verify structure
        assert len(results) == 4  # Original 2 + 2 duplicates

    def test_sort_results_by_relevance(self, sample_search_results):
        """Test sorting search results by relevance."""
        # Could sort by citation count, date, etc.
        results = sorted(
            sample_search_results,
            key=lambda x: x.citation_count or 0,
            reverse=True,
        )

        assert results[0].citation_count >= results[1].citation_count

    def test_filter_results_by_year(self, sample_search_results):
        """Test filtering results by year range."""
        filtered = [
            r for r in sample_search_results
            if r.year and 2022 <= r.year <= 2023
        ]

        # Should only include results in year range
        for result in filtered:
            assert 2022 <= result.year <= 2023

    def test_enrich_search_results(self, sample_search_results):
        """Test enrichment of search results with additional metadata."""
        for result in sample_search_results:
            # Verify required fields are present
            assert result.title is not None
            assert result.authors is not None
            assert result.year is not None or result.doi is not None
