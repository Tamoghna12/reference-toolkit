"""Tests for security validation functions."""

import pytest
from pathlib import Path
from reference_toolkit.security import (
    validate_email,
    validate_url,
    validate_doi,
    validate_path_safe,
    sanitize_filename,
    sanitize_input,
    validate_proxy_url,
    validate_csv_input,
    check_file_size_limit,
)


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_emails(self):
        """Test that valid email addresses pass validation."""
        valid_emails = [
            "user@example.com",
            "test.user@example.co.uk",
            "first+last@domain.edu",
            "user123@test.org",
            "admin@mail.company.com",
        ]
        for email in valid_emails:
            assert validate_email(email) is True, f"Should validate: {email}"

    def test_invalid_emails(self):
        """Test that invalid email addresses fail validation."""
        invalid_emails = [
            "",
            "not-an-email",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com",
            None,
            123,
            [],
        ]
        for email in invalid_emails:
            assert validate_email(email) is False, f"Should reject: {email}"


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_urls(self):
        """Test that valid URLs pass validation."""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://api.example.com/v1/endpoint",
            "http://localhost:8080",
            "https://example.com:443/path?query=value",
        ]
        for url in valid_urls:
            is_valid, error = validate_url(url)
            assert is_valid is True, f"Should validate: {url}, error: {error}"
            assert error == ""

    def test_invalid_urls(self):
        """Test that invalid URLs fail validation."""
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com",
            "example.com",
            "//example.com",
            None,
        ]
        for url in invalid_urls:
            is_valid, error = validate_url(url)
            assert is_valid is False, f"Should reject: {url}"
            assert error != ""


class TestValidateDOI:
    """Tests for DOI validation."""

    def test_valid_dois(self):
        """Test that valid DOIs pass validation."""
        valid_dois = [
            "10.1038/s41592-023-01000-0",
            "10.1234/doi.suffix",
            "10.1234/example.doi",
            "10.1000/182",
        ]
        for doi in valid_dois:
            is_valid, error = validate_doi(doi)
            assert is_valid is True, f"Should validate: {doi}, error: {error}"
            assert error == ""

    def test_invalid_dois(self):
        """Test that invalid DOIs fail validation."""
        invalid_dois = [
            "",
            "not-a-doi",
            "11.1234/invalid",  # Wrong prefix
            "10.123/invalid",   # Prefix too short
            "10.1234",          # Missing suffix
            None,
        ]
        for doi in invalid_dois:
            is_valid, error = validate_doi(doi)
            assert is_valid is False, f"Should reject: {doi}"
            assert error != ""


class TestValidatePathSafe:
    """Tests for path traversal validation."""

    def test_safe_paths(self):
        """Test that safe paths pass validation."""
        safe_paths = [
            Path("safe_file.txt"),
            Path("folder/subfolder/file.txt"),
            Path("./relative.txt"),
        ]
        for path in safe_paths:
            is_valid, error = validate_path_safe(path, allow_traversal=False)
            assert is_valid is True, f"Should validate: {path}, error: {error}"
            assert error == ""

    def test_path_traversal_rejected(self):
        """Test that path traversal attempts are rejected."""
        dangerous_paths = [
            Path("../../../etc/passwd"),
            Path("../../../../secret.txt"),
            Path("../parent/file.txt"),
        ]
        for path in dangerous_paths:
            is_valid, error = validate_path_safe(path, allow_traversal=False)
            assert is_valid is False, f"Should reject traversal: {path}"
            assert "traversal" in error.lower()

    def test_traversal_allowed_when_flag_set(self):
        """Test that traversal is allowed when flag is set."""
        traversal_path = Path("../parent/file.txt")
        is_valid, error = validate_path_safe(traversal_path, allow_traversal=True)
        assert is_valid is True, f"Should allow traversal with flag: {traversal_path}"

    def test_null_bytes_rejected(self):
        """Test that null bytes in paths are rejected."""
        null_byte_path = Path("file\x00.txt")
        is_valid, error = validate_path_safe(null_byte_path)
        assert is_valid is False
        assert "null byte" in error.lower()


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_basic_sanitization(self):
        """Test basic dangerous character removal."""
        dangerous_names = [
            ("file:name?.txt", "file_name_.txt"),
            ("file<>name.txt", "filename.txt"),
            ('file"name|txt', "filenametxt"),
            ("file*name.txt", "filename.txt"),
        ]
        for input_name, expected_substring in dangerous_names:
            result = sanitize_filename(input_name)
            assert ":" not in result
            assert "?" not in result
            assert "<" not in result
            assert ">" not in result
            assert "|" not in result
            assert "*" not in result

    def test_path_separator_replacement(self):
        """Test that path separators are replaced."""
        result = sanitize_filename("folder/file.txt")
        assert "/" not in result
        assert "\\" not in result

    def test_null_byte_removal(self):
        """Test that null bytes are removed."""
        result = sanitize_filename("file\x00name.txt")
        assert "\x00" not in result

    def test_length_limiting(self):
        """Test that overly long filenames are truncated."""
        long_name = "a" * 300
        result = sanitize_filename(long_name, max_length=100)
        assert len(result) <= 100

    def test_empty_input(self):
        """Test that empty input returns 'unknown'."""
        assert sanitize_filename("") == "unknown"
        assert sanitize_filename(None) == "unknown"

    def test_leading_trailing_dots_removed(self):
        """Test that leading/trailing dots and spaces are removed."""
        assert sanitize_filename("  .test.  ") == "test"


class TestSanitizeInput:
    """Tests for input sanitization."""

    def test_xss_prevention(self):
        """Test that XSS attempts are neutralized."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "<iframe src='malicious.com'></iframe>",
        ]
        for attempt in xss_attempts:
            result = sanitize_input(attempt)
            assert "<script>" not in result
            assert "<img" not in result
            assert "<iframe" not in result
            assert "&lt;" in result or "&gt;" in result

    def test_length_limiting(self):
        """Test that input is length-limited."""
        long_input = "a" * 20000
        result = sanitize_input(long_input, max_length=100)
        assert len(result) == 100

    def test_null_byte_removal(self):
        """Test that null bytes are removed."""
        result = sanitize_input("test\x00string")
        assert "\x00" not in result

    def test_empty_input(self):
        """Test that empty input returns empty string."""
        assert sanitize_input("") == ""
        assert sanitize_input(None) == ""


class TestValidateProxyUrl:
    """Tests for proxy URL validation."""

    def test_valid_proxy_urls(self):
        """Test that valid proxy URLs pass validation."""
        valid_proxies = [
            "http://proxy.example.com:8080",
            "https://proxy.example.com:3128",
            "http://localhost:8888",
            "http://192.168.1.1:8080",
        ]
        for proxy in valid_proxies:
            is_valid, error = validate_proxy_url(proxy)
            assert is_valid is True, f"Should validate: {proxy}, error: {error}"
            assert error == ""

    def test_invalid_proxy_urls(self):
        """Test that invalid proxy URLs fail validation."""
        invalid_proxies = [
            "",
            "not-a-proxy",
            "ftp://proxy.example.com:8080",
            "http://proxy.example.com:99999",  # Invalid port
            "http://proxy.example.com:0",      # Invalid port
        ]
        for proxy in invalid_proxies:
            is_valid, error = validate_proxy_url(proxy)
            assert is_valid is False, f"Should reject: {proxy}"
            assert error != ""

    def test_credentials_warning(self):
        """Test that credentials in URL generate warning."""
        credential_proxies = [
            "http://user:pass@proxy.example.com:8080",
            "https://user@proxy.example.com:8080",
        ]
        for proxy in credential_proxies:
            is_valid, error = validate_proxy_url(proxy)
            assert is_valid is True, f"Should validate but warn: {proxy}"
            assert "WARNING" in error or "credentials" in error.lower()


class TestValidateCSVInput:
    """Tests for CSV input validation."""

    def test_valid_csv(self):
        """Test that valid CSV passes validation."""
        valid_csv = "title,authors,year\nTest,Author,2023"
        is_valid, error = validate_csv_input(valid_csv)
        assert is_valid is True, f"Should validate CSV, error: {error}"
        assert error == ""

    def test_empty_csv(self):
        """Test that empty CSV fails validation."""
        is_valid, error = validate_csv_input("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_csv_missing_rows(self):
        """Test that CSV with only header fails validation."""
        is_valid, error = validate_csv_input("title,authors,year")
        assert is_valid is False
        assert "must have" in error.lower() or "at least one row" in error.lower()

    def test_suspiciously_long_line(self):
        """Test that suspiciously long CSV lines are rejected."""
        long_line = "a" * 100001
        is_valid, error = validate_csv_input(f"header\n{long_line}")
        assert is_valid is False
        assert "suspiciously long" in error.lower()

    def test_null_bytes_rejected(self):
        """Test that null bytes in CSV are rejected."""
        is_valid, error = validate_csv_input("header\nrow\x00with\x00nulls")
        assert is_valid is False
        assert "null byte" in error.lower()


class TestCheckFileSizeLimit:
    """Tests for file size limit checking."""

    def test_nonexistent_file(self):
        """Test that nonexistent files pass validation."""
        nonexistent = Path("/this/file/does/not/exist.txt")
        is_valid, error = check_file_size_limit(nonexistent)
        assert is_valid is True  # Non-existent files are handled elsewhere

    def test_small_file_within_limit(self, tmp_path):
        """Test that small files pass validation."""
        small_file = tmp_path / "small.txt"
        small_file.write_text("small content")
        is_valid, error = check_file_size_limit(small_file, max_size_mb=1.0)
        assert is_valid is True, f"Should accept small file, error: {error}"
        assert error == ""

    def test_large_file_exceeds_limit(self, tmp_path):
        """Test that large files fail validation."""
        large_file = tmp_path / "large.txt"
        # Create a 2MB file
        large_file.write_bytes(b"x" * (2 * 1024 * 1024))
        is_valid, error = check_file_size_limit(large_file, max_size_mb=1.0)
        assert is_valid is False
        assert "too large" in error.lower()
