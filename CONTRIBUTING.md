# Contributing to Reference Toolkit

Thank you for your interest in contributing to the Reference Toolkit! This document provides guidelines for contributing.

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
git clone https://github.com/your-username/reference-toolkit.git
cd reference-toolkit
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -e .
pip install pytest pytest-cov flake8 mypy black isort
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/reference_toolkit

# Run specific test file
pytest tests/test_pdf_renamer.py
```

## Code Style

### Python Style Guide

We follow **PEP 8** style guidelines with some modifications:

- **Line length**: Maximum 100 characters (soft limit)
- **Imports**: Group imports (stdlib, third-party, local)
- **Type hints**: Required for all functions
- **Docstrings**: Google style docstrings

### Formatting

Use **Black** and **isort** for consistent formatting:

```bash
# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/
```

### Linting

Run **flake8** before committing:

```bash
flake8 src/ tests/
```

### Type Checking

Run **mypy** for type checking:

```bash
mypy src/reference_toolkit
```

## Project Structure

```
reference-toolkit/
├── src/reference_toolkit/    # Source code
│   ├── __init__.py
│   ├── cli.py               # CLI commands
│   ├── config.py            # Configuration
│   └── ...
├── tests/                    # Test suite
│   ├── test_*.py
│   └── fixtures/            # Test fixtures
├── examples/                 # Example scripts
├── docs/                     # Documentation
├── .github/workflows/        # CI/CD
└── pyproject.toml           # Project config
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Write clear, concise code
- Add type hints
- Include docstrings
- Add/update tests

### 3. Test Your Changes

```bash
# Run tests
pytest

# Check formatting
black --check src/ tests/
isort --check-only src/ tests/

# Run linting
flake8 src/ tests/
```

### 4. Commit Changes

Follow **Conventional Commits** specification:

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: refactor code
style: formatting changes
chore: maintenance tasks
```

Example:

```bash
git commit -m "feat: add support for PDF metadata extraction from first page"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title and description
- Reference related issues
- Screenshots if applicable

## Adding Features

### New CLI Commands

1. Add command function in `cli.py`
2. Add subparser with arguments
3. Implement feature in appropriate module
4. Add tests in `tests/test_cli.py`
5. Update documentation

### New Modules

1. Create module in `src/reference_toolkit/`
2. Add type hints and docstrings
3. Add tests in `tests/`
4. Import in `__init__.py` if needed
5. Update documentation

## Testing Guidelines

### Test Structure

```python
def test_specific_behavior():
    """Test that specific behavior works as expected."""
    # Arrange
    input_data = setup()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

### Test Fixtures

Use pytest fixtures for common setup:

```python
@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {"key": "value"}
```

### Integration Tests

Mark integration tests:

```python
@pytest.mark.integration
def test_with_external_service():
    """Test integration with external service."""
    # Test code here
```

Run only unit tests:
```bash
pytest -m "not integration"
```

## Documentation

### Docstring Format

Use Google style docstrings:

```python
def extract_metadata(pdf_path: Path) -> PDFMetadata:
    """Extract metadata from a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        PDFMetadata object with extracted information.

    Raises:
        FileNotFoundError: If PDF file doesn't exist.
        PDFReadError: If PDF file is corrupted.
    """
    pass
```

### Updating Documentation

- **User docs**: Update relevant files in `docs/`
- **API docs**: Add/update docstrings
- **README**: Update for new features
- **Examples**: Add usage examples in `examples/`

## Pull Request Review

### Before Submitting

- [ ] Tests pass locally
- [ ] Code formatted with black/isort
- [ ] No linting errors
- [ ] Type hints added
- [ ] Docstrings added
- [ ] Documentation updated
- [ ] Tests added for new features

### Review Process

1. Automated tests must pass
2. Code review by maintainers
3. Address review feedback
4. Approval required for merge

## Getting Help

### Questions?

- Open a discussion on GitHub
- Check existing issues
- Read documentation

### Bugs?

- Search existing issues
- Create new issue with:
  - Clear description
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details

### Feature Requests?

- Check existing requests
- Create new issue with:
  - Use case description
  - Proposed solution
  - Alternatives considered

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Welcome new contributors
- Focus on what is best for the community

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Reference Toolkit! 🎉
