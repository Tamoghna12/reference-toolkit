# Changelog

All notable changes to Reference Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and organization
- Comprehensive test suite with pytest
- CI/CD pipeline with GitHub Actions
- Contributing guidelines

## [2.0.0] - 2026-03-15

### Added
- **PDF Batch Renaming**: New `rename` command for renaming PDF files using metadata
  - Works on ANY PDF folder (not just downloads)
  - Smart metadata extraction (PDF metadata → first page text → DOI)
  - Safety features: dry-run mode, copy to new directory
  - Duplicate filename handling with counter suffixes
  - Character sanitization for filesystem safety

- **Enhanced PDF Access**:
  - Preprint search (arXiv, bioRxiv, medRxiv, PMC)
  - Semantic Scholar integration
  - PDF quality validation (corruption, encryption, text content checks)
  - Smart rate limiting with exponential backoff

- **Docker Support**:
  - Multi-stage Docker build
  - Production-ready 291MB image
  - Non-root user configuration
  - Docker Compose support

- **Documentation**:
  - PDF_RENAMING_GUIDE.md - Complete guide for PDF renaming
  - DOCKER_USAGE.md - Docker quick reference
  - ENHANCED_ACCESS_FEATURES.md - Enhanced features documentation
  - VERIFICATION_REPORT.md - Fact-check audit (49 claims verified)

### Changed
- Improved error handling throughout codebase
- Enhanced type hints coverage
- Better logging with appropriate levels
- Updated all command help texts
- Restructured project following Python best practices

### Fixed
- Rate limit errors with exponential backoff
- Docker image size documentation (actual: 291MB)
- Missing `contacts` command in README

### Technical
- 7,301+ lines of production code
- 2,500+ lines of documentation
- 32 files committed
- Python 3.10+ support
- Type hints throughout
- Comprehensive docstrings

## [1.0.0] - Initial Release

### Added
- Core CLI commands: search, resolve, download, pipeline, convert
- Reference parsing from multiple formats (EndNote, Mendeley, BibTeX, RIS)
- DOI resolution via Crossref
- PDF downloading via Unpaywall
- Export to CSV, BibTeX, JSON
- Author contact extraction
- Basic rate limiting
- Logging functionality

### Features
- **search**: Find papers via Google Scholar, PubMed, Crossref
- **resolve**: Match citations to DOIs with confidence scoring
- **download**: Get open-access PDFs
- **pipeline**: Full workflow automation
- **convert**: Format conversion
- **contacts**: Extract corresponding author information

---

## Version History Summary

| Version | Date | Major Changes |
|---------|------|---------------|
| 2.0.0 | 2026-03-15 | PDF renaming, enhanced access, Docker support |
| 1.0.0 | TBD | Initial release with core functionality |

---

## Upgrade Notes

### From 1.0.0 to 2.0.0

**Breaking Changes**: None

**New Features**:
- `reftool rename` command for PDF batch renaming
- Enhanced PDF access with preprint search
- Docker support

**Migration**:
- No migration needed - all changes are backwards compatible
- Simply upgrade: `pip install --upgrade reference-toolkit`

---

## Future Releases

See [FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md) for planned features.
