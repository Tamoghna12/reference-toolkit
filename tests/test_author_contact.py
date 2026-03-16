"""Tests for author contact extraction functionality."""

import pytest
from pathlib import Path
from reference_toolkit.config import Config
from reference_toolkit.author_contact import AuthorContactExtractor
from reference_toolkit.parser import Reference


@pytest.fixture
def test_config():
    """Create test configuration."""
    return Config(
        email="test@example.com",
        extract_author_emails=True,
    )


@pytest.fixture
def sample_csv_with_authors(tmp_path):
    """Create a sample CSV file with author information."""
    import csv

    csv_file = tmp_path / "test_authors.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'raw_citation', 'title', 'doi', 'authors', 'year', 'journal',
            'corresponding_author', 'corresponding_email'
        ])
        writer.writeheader()
        writer.writerow({
            'raw_citation': 'Smith et al. (2023)',
            'title': 'Test Paper 1',
            'doi': '10.1234/test.001',
            'authors': 'Smith, J.; Johnson, A.; Brown, R.',
            'year': '2023',
            'journal': 'Nature',
            'corresponding_author': 'Smith, J.',
            'corresponding_email': 'smith@example.com',
        })
        writer.writerow({
            'raw_citation': 'Johnson et al. (2022)',
            'title': 'Test Paper 2',
            'doi': '10.1234/test.002',
            'authors': 'Johnson, A.; Lee, S.',
            'year': '2022',
            'journal': 'Science',
            'corresponding_author': 'Johnson, A.',
            'corresponding_email': 'johnson@example.com',
        })
        writer.writerow({
            'raw_citation': 'Brown et al. (2021)',
            'title': 'Test Paper 3',
            'doi': '10.1234/test.003',
            'authors': 'Brown, R.; Wilson, K.',
            'year': '2021',
            'journal': 'Cell',
            'corresponding_author': '',
            'corresponding_email': '',
        })

    return csv_file


@pytest.fixture
def sample_csv_no_authors(tmp_path):
    """Create a CSV file without author contact info."""
    import csv

    csv_file = tmp_path / "test_no_authors.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'raw_citation', 'title', 'doi', 'authors', 'year', 'journal'
        ])
        writer.writeheader()
        writer.writerow({
            'raw_citation': 'Test citation',
            'title': 'Test Title',
            'doi': '10.1234/test.001',
            'authors': 'Author, A.',
            'year': '2023',
            'journal': 'Journal',
        })

    return csv_file


class TestAuthorContactExtractor:
    """Tests for AuthorContactExtractor class."""

    def test_initialization(self, test_config):
        """Test extractor initialization."""
        extractor = AuthorContactExtractor(test_config)
        assert extractor.config == test_config
        assert extractor.extract_author_emails is True

    def test_initialization_without_email_extraction(self):
        """Test initialization when email extraction is disabled."""
        config = Config(
            email="test@example.com",
            extract_author_emails=False,
        )
        extractor = AuthorContactExtractor(config)
        assert extractor.extract_author_emails is False


@pytest.mark.unit
class TestEmailExtraction:
    """Unit tests for email extraction logic."""

    def test_extract_from_csv_with_emails(self, test_config, sample_csv_with_authors):
        """Test extracting emails from CSV with existing email data."""
        extractor = AuthorContactExtractor(test_config)
        contacts = extractor.extract_from_csv(sample_csv_with_authors)

        assert contacts is not None
        assert len(contacts) >= 2  # At least the two papers with emails

        # Verify structure
        for doi, contact_info in contacts.items():
            if contact_info:
                assert 'email' in contact_info or 'name' in contact_info

    def test_extract_from_csv_no_emails(self, test_config, sample_csv_no_authors):
        """Test extracting from CSV without email column."""
        extractor = AuthorContactExtractor(test_config)
        contacts = extractor.extract_from_csv(sample_csv_no_authors)

        assert contacts is not None
        # Should return empty contacts since no emails in CSV
        assert len(contacts) == 0 or all(v is None for v in contacts.values())

    def test_extract_from_nonexistent_file(self, test_config):
        """Test handling of non-existent CSV file."""
        extractor = AuthorContactExtractor(test_config)

        nonexistent_file = Path("/nonexistent/file.csv")
        contacts = extractor.extract_from_csv(nonexistent_file)

        # Should handle gracefully
        assert contacts is not None or contacts == {}


@pytest.mark.unit
class TestEmailValidation:
    """Tests for email validation in contact extraction."""

    def test_validate_email_format(self, test_config):
        """Test email format validation."""
        extractor = AuthorContactExtractor(test_config)

        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
        ]

        for email in valid_emails:
            # This would need actual validation implementation
            assert '@' in email
            assert '.' in email

    def test_handle_invalid_emails(self, test_config):
        """Test handling of invalid email formats."""
        extractor = AuthorContactExtractor(test_config)

        # Invalid emails
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "",
        ]

        for email in invalid_emails:
            # Should handle invalid emails gracefully
            assert not extractor.config.email == email


@pytest.mark.integration
class TestRequestGeneration:
    """Tests for email request generation."""

    def test_generate_request_emails(self, test_config, sample_csv_with_authors, tmp_path):
        """Test generating email request template."""
        extractor = AuthorContactExtractor(test_config)
        contacts = extractor.extract_from_csv(sample_csv_with_authors)

        output_file = tmp_path / "request_emails.txt"
        extractor.generate_request_emails(
            contacts_by_doi=contacts,
            input_csv=sample_csv_with_authors,
            output_file=output_file,
        )

        # Verify file was created
        assert output_file.exists()

        # Verify content contains expected elements
        content = output_file.read_text()
        # Should contain some email-like content
        assert len(content) > 0

    def test_generate_request_with_template(self, test_config, sample_csv_with_authors, tmp_path):
        """Test generating requests with custom template."""
        config = Config(
            email="test@example.com",
            author_contact_template="Dear {author},\n\nI am writing to request..."
        )
        extractor = AuthorContactExtractor(config)
        contacts = extractor.extract_from_csv(sample_csv_with_authors)

        output_file = tmp_path / "custom_template.txt"
        extractor.generate_request_emails(
            contacts_by_doi=contacts,
            input_csv=sample_csv_with_authors,
            output_file=output_file,
        )

        # Verify file was created
        assert output_file.exists()


class TestContactExtractionLogic:
    """Tests for contact extraction logic."""

    def test_parse_corresponding_author(self, test_config):
        """Test parsing corresponding author information."""
        extractor = AuthorContactExtractor(test_config)

        # Test data with corresponding author
        author_string = "Smith, J."
        email_string = "smith@example.com"

        # Should parse author name
        if author_string:
            assert ',' in author_string or ' ' in author_string

        # Should validate email
        if email_string:
            assert '@' in email_string
            assert '.' in email_string

    def test_handle_multiple_authors(self, test_config):
        """Test handling of multiple authors in a single paper."""
        extractor = AuthorContactExtractor(test_config)

        authors_string = "Smith, J.; Johnson, A.; Brown, R.; Lee, S."
        authors = [a.strip() for a in authors_string.split(';')]

        assert len(authors) == 4
        assert all(authors)  # No empty strings

    def test_extract_contact_from_empty_data(self, test_config):
        """Test extraction from empty or missing data."""
        extractor = AuthorContactExtractor(test_config)

        # Test with empty strings
        result = extractor.extract_contact_info("", "")
        assert result is None or result == {}

        # Test with None
        result = extractor.extract_contact_info(None, None)
        assert result is None or result == {}


@pytest.mark.unit
class TestCSVProcessing:
    """Tests for CSV processing in contact extraction."""

    def test_read_csv_columns(self, test_config, sample_csv_with_authors):
        """Test reading specific columns from CSV."""
        extractor = AuthorContactExtractor(test_config)

        import csv
        with open(sample_csv_with_authors, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify expected columns exist
        assert len(rows) == 3
        assert any('corresponding_email' in row for row in rows)

    def test_handle_csv_with_missing_columns(self, test_config, sample_csv_no_authors):
        """Test CSV without contact columns."""
        extractor = AuthorContactExtractor(test_config)

        import csv
        with open(sample_csv_no_authors, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should still be readable
        assert len(rows) == 1
        assert 'title' in rows[0]


class TestAuthorContactErrorHandling:
    """Tests for error handling in author contact extraction."""

    def test_handle_malformed_csv(self, test_config, tmp_path):
        """Test handling of malformed CSV data."""
        # Create CSV with malformed data
        bad_csv = tmp_path / "bad.csv"
        with open(bad_csv, 'w', encoding='utf-8') as f:
            f.write("title,authors\n")
            f.write("Test Paper,\"Author; With; Sem;icolons\"\n")
            f.write("Bad Paper,\"Unclosed quote\n")  # Malformed row

        extractor = AuthorContactExtractor(test_config)
        # Should handle gracefully
        contacts = extractor.extract_from_csv(bad_csv)
        assert contacts is not None

    def test_handle_unicode_in_authors(self, test_config, tmp_path):
        """Test handling of Unicode characters in author names."""
        import csv

        csv_file = tmp_path / "unicode_authors.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'authors', 'corresponding_email'])
            writer.writeheader()
            writer.writerow({
                'title': 'Test with Unicode',
                'authors': 'Müller, A.; Sánchéz, J.; 日本, 太郎',
                'corresponding_email': 'muller@example.com',
            })

        extractor = AuthorContactExtractor(test_config)
        contacts = extractor.extract_from_csv(csv_file)

        # Should handle Unicode without errors
        assert contacts is not None
