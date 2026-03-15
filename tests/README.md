# Tests

This directory contains the test suite for the Reference Toolkit.

## Test Structure

```
tests/
├── __init__.py                # Test package initialization
├── test_cli.py                # CLI command tests
├── test_pdf_renamer.py        # PDF renaming functionality tests
├── integration/               # Integration tests
│   ├── test_proxy.py         # Proxy configuration tests
│   └── test_with_vpn.py      # VPN download tests
└── fixtures/                  # Test fixtures and sample data
    ├── sample_refs.txt       # Sample reference list (EndNote/Mendeley format)
    ├── sample_refs.bib       # Sample BibTeX file
    └── test_pdfs/            # Directory for test PDF files (optional)
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_pdf_renamer.py
```

### Run with Coverage
```bash
pytest --cov=src/reference_toolkit --cov-report=term-missing
```

### Run Only Unit Tests (Skip Integration)
```bash
pytest -m "not integration"
```

### Run with Verbose Output
```bash
pytest -v
```

## Test Fixtures

### Sample Reference Files

- **sample_refs.txt** - Plain text reference list (EndNote/Mendeley format)
- **sample_refs.bib** - BibTeX format references

### Test PDFs

Place test PDF files in `tests/fixtures/test_pdfs/` for integration testing.

## Test Categories

### Unit Tests
- `test_cli.py` - Tests for CLI commands and argument parsing
- `test_pdf_renamer.py` - Tests for PDF metadata extraction and renaming

### Integration Tests
- `integration/test_proxy.py` - Tests for proxy configuration
- `integration/test_with_vpn.py` - Tests for VPN-based downloads

Run integration tests with:
```bash
pytest tests/integration/
```

## Markers

Tests can be marked with specific markers:

- `@pytest.mark.integration` - Integration tests requiring external services
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.network` - Tests requiring network access

Run tests by marker:
```bash
pytest -m integration  # Only integration tests
pytest -m "not network"  # Skip network tests
```

## Adding New Tests

1. Create test file in `tests/` directory
2. Use pytest fixtures for common setup
3. Follow naming convention: `test_*.py`
4. Use descriptive test function names: `test_specific_behavior()`

Example:
```python
def test_specific_feature():
    """Test that specific feature works as expected."""
    # Arrange
    input_data = setup()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

## Coverage Goals

- **Unit tests**: 80%+ coverage
- **Integration tests**: Critical paths covered
- **CLI commands**: All commands tested

## Troubleshooting

### Tests Fail Due to Missing Dependencies
```bash
pip install -e ".[dev]"
```

### Tests Fail Due to Network Issues
Skip integration tests:
```bash
pytest -m "not integration"
```

### Tests Fail Due to Missing Fixtures
Ensure test fixtures are in `tests/fixtures/`
