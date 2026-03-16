"""Security utilities for input validation and sanitization."""

import re
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple


def validate_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid, False otherwise

    Examples:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid")
        False
        >>> validate_email("")
        False
    """
    if not email or not isinstance(email, str):
        return False

    # Basic email format validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False

    # Additional security checks: reject problematic patterns
    # Reject consecutive dots (security risk, unusual in practice)
    if '..' in email:
        return False

    # Reject dots at start or end of local part
    local_part = email.split('@')[0]
    if local_part.startswith('.') or local_part.endswith('.'):
        return False

    return True


def validate_url(url: str) -> Tuple[bool, str]:
    """Validate URL format and structure.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_url("https://example.com")
        (True, "")
        >>> validate_url("not a url")
        (False, "Invalid URL format")
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty"

    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.scheme in ['http', 'https']:
            return False, "URL must use http or https scheme"
        if not parsed.netloc:
            return False, "URL must have a network location"
        return True, ""
    except Exception as e:
        return False, f"URL parsing error: {e}"


def validate_doi(doi: str) -> Tuple[bool, str]:
    """Validate DOI (Digital Object Identifier) format.

    Args:
        doi: DOI string to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_doi("10.1038/s41592-023-01000-0")
        (True, "")
        >>> validate_doi("invalid")
        (False, "Invalid DOI format")
    """
    if not doi or not isinstance(doi, str):
        return False, "DOI cannot be empty"

    # DOI pattern: 10. + prefix + suffix
    # Common patterns: 10.1234/doi.suffix, 10.1234/example.doi
    patterns = [
        r'^10\.\d{4,}/[^\s]+$',
        r'^10\.\d{4,}/[^\s]+\.[^\s]+$',  # With suffix
    ]

    for pattern in patterns:
        if re.match(pattern, doi.strip()):
            return True, ""

    return False, "Invalid DOI format (expected format: 10.1234/...)"


def validate_path_safe(path: Path, allow_traversal: bool = False) -> Tuple[bool, str]:
    """Validate that a path is safe for filesystem operations.

    Args:
        path: Path to validate
        allow_traversal: Whether to allow parent directory traversal

    Returns:
        Tuple of (is_safe, error_message)

    Examples:
        >>> validate_path_safe(Path("safe_file.txt"))
        (True, "")
        >>> validate_path_safe(Path("../../../etc/passwd"))
        (False, "Path traversal detected")
    """
    if not path:
        return False, "Path cannot be empty"

    try:
        # Resolve to absolute path
        resolved = path.resolve()
        current_dir = Path.cwd()

        # Check for path traversal
        if not allow_traversal:
            try:
                resolved.relative_to(current_dir)
            except ValueError:
                return False, "Path traversal detected: references parent directory"

        # Check for suspicious patterns (only when traversal not allowed)
        path_str = str(path)
        if not allow_traversal and ('../' in path_str or '..\\' in path_str):
            return False, "Path contains traversal patterns"

        # Check for null bytes (Windows exploit)
        if '\x00' in path_str:
            return False, "Path contains null bytes"

        return True, ""

    except Exception as e:
        return False, f"Path validation error: {e}"


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename to be filesystem-safe.

    Args:
        filename: Original filename
        max_length: Maximum length for filename

    Returns:
        Sanitized filename

    Examples:
        >>> sanitize_filename("file:name?.txt")
        'file_name_.txt'
        >>> sanitize_filename("Very long filename " * 100)
        'Very_long_filename'
    """
    if not filename:
        return "unknown"

    # Replace path separators
    sanitized = filename.replace('/', '_').replace('\\', '_')

    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')

    # Remove/replace problematic characters
    # Keep alphanumeric, underscores, hyphens, dots, spaces
    sanitized = re.sub(r'[<>:"|?*\x00-\x1f]', '', sanitized)

    # Collapse multiple spaces to single space
    sanitized = re.sub(r'\s+', ' ', sanitized)

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')

    # Limit length
    if len(sanitized) > max_length:
        # Try to cut at word boundary
        sanitized = sanitized[:max_length]
        sanitized = re.sub(r'\s+$', '', sanitized)  # Remove trailing space
        sanitized = sanitized.rstrip('.')

    return sanitized or "unknown"


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input to prevent injection attacks.

    Args:
        text: User input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text

    Examples:
        >>> sanitize_input("Hello <script>alert('xss')</script>")
        'Hello &lt;script&gt;alert(\\'xss\\')&lt;/script&gt;'
        >>> sanitize_input("Normal text")
        'Normal text'
    """
    if not text:
        return ""

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove null bytes
    text = text.replace('\x00', '')

    # HTML escape (basic XSS prevention)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    return text


def validate_proxy_url(proxy_url: str) -> Tuple[bool, str]:
    """Validate proxy URL format and credentials.

    Args:
        proxy_url: Proxy URL to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_proxy_url("http://proxy.example.com:8080")
        (True, "")
        >>> validate_proxy_url("invalid-url")
        (False, "Invalid proxy URL format")
    """
    if not proxy_url:
        return False, "Proxy URL cannot be empty"

    # Validate URL format
    is_valid, error_msg = validate_url(proxy_url)
    if not is_valid:
        return False, error_msg

    try:
        parsed = urllib.parse.urlparse(proxy_url)

        # Check for valid port range (including port 0 which is invalid)
        # Extract port manually since parsed.port returns None for 0
        if ':' in parsed.netloc:
            # Split the netloc to get port
            port_str = parsed.netloc.split(':')[-1]
            # Remove any credentials prefix
            if '@' in port_str:
                port_str = port_str.split('@')[-1]
            # Remove any path suffix
            port_str = port_str.split('/')[0]

            try:
                port = int(port_str)
                if not (1 <= port <= 65535):
                    return False, f"Invalid port number: {port}"
            except ValueError:
                pass  # Not a valid port number, will be caught by URL validation

        # Warn if credentials in URL (security concern)
        if '@' in parsed.netloc:
            return True, "WARNING: Credentials in proxy URL may be exposed in logs"

        return True, ""

    except Exception as e:
        return False, f"Proxy validation error: {e}"


def validate_csv_input(data: str) -> Tuple[bool, str]:
    """Validate CSV input for basic safety.

    Args:
        data: CSV data string

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_csv_input("title,authors,year\\nTest,Author,2023")
        (True, "")
        >>> validate_csv_input("")
        (False, "CSV data is empty")
    """
    if not data:
        return False, "CSV data is empty"

    # Basic checks
    lines = data.split('\n')
    if len(lines) < 2:
        return False, "CSV data must have header and at least one row"

    # Check for suspiciously long lines (potential DoS)
    for line in lines:
        if len(line) > 100000:  # 100KB per line
            return False, f"Suspiciously long CSV line ({len(line)} characters)"

    # Check for null bytes
    if '\x00' in data:
        return False, "CSV data contains null bytes"

    return True, ""


def check_file_size_limit(file_path: Path, max_size_mb: float = 100.0) -> Tuple[bool, str]:
    """Check if file size is within acceptable limits.

    Args:
        file_path: Path to file to check
        max_size_mb: Maximum file size in megabytes

    Returns:
        Tuple of (is_within_limit, error_message)

    Examples:
        >>> check_file_size_limit(Path("small.txt"), 100)
        (True, "")
        >>> check_file_size_limit(Path("huge.txt"), 0.001)
        (False, "File exceeds size limit")
    """
    if not file_path.exists():
        return True, ""  # Non-existent files are handled elsewhere

    try:
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        if size_mb > max_size_mb:
            return False, f"File too large ({size_mb:.1f}MB > {max_size_mb}MB limit)"

        return True, ""

    except Exception as e:
        return False, f"Error checking file size: {e}"
