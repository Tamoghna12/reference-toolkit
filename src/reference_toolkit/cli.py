#!/usr/bin/env python3
"""Command-line interface for the Reference Toolkit.

A comprehensive tool for:
- Discovering papers via search (Google Scholar, PubMed, Crossref)
- Parsing reference lists from multiple formats (EndNote, Mendeley, BibTeX, RIS)
- Resolving citations to DOIs via Crossref
- Downloading open-access PDFs via Unpaywall
- Exporting to BibTeX/CSV/JSON
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from reference_toolkit.config import Config, OutputFormat, SearchSource, Columns
from reference_toolkit.parser import ReferenceParser, ReferenceFormat, Reference
from reference_toolkit.search import SearchEngine, SearchResult
from reference_toolkit.crossref import CrossrefClient
from reference_toolkit.unpaywall import UnpaywallClient
from reference_toolkit.doi_resolver import DOIResolver
from reference_toolkit.pdf_downloader import PDFDownloader
from reference_toolkit.exporter import CSVExporter, BibTeXExporter, JSONExporter
from reference_toolkit.author_contact import AuthorContactExtractor
from reference_toolkit.pdf_renamer import PDFRenamer

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, log_file: Path | None = None):
    """Configure logging output."""
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, mode="a"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


# =============================================================================
# SEARCH COMMAND
# =============================================================================

def cmd_search(args: argparse.Namespace) -> int:
    """Search for papers and export results."""
    config = Config(
        email=args.mailto,
        search_limit=args.limit,
        search_year_start=args.year_start,
        search_year_end=args.year_end,
    )

    setup_logging(verbose=args.verbose, log_file=Path("search.log"))

    source_map = {
        "all": SearchSource.ALL,
        "scholar": SearchSource.GOOGLE_SCHOLAR,
        "pubmed": SearchSource.PUBMED,
        "crossref": SearchSource.CROSSREF,
    }

    engine = SearchEngine(config)

    logger.info("=" * 60)
    logger.info("Paper Search")
    logger.info(f"Query: {args.query}")
    logger.info(f"Sources: {args.source}")
    logger.info(f"Limit: {args.limit}")
    logger.info("=" * 60)

    start = datetime.now()
    results = engine.search(
        query=args.query,
        sources=source_map.get(args.source, SearchSource.ALL),
        year_start=args.year_start,
        year_end=args.year_end,
        limit=args.limit,
    )

    elapsed = datetime.now() - start

    # Export results
    output_path = Path(args.output)

    if args.format == "bibtex":
        with BibTeXExporter(output_path) as exporter:
            for r in results:
                ref = Reference(
                    citation=r.to_citation(),
                    title=r.title,
                    authors=r.authors,
                    year=r.year,
                    journal=r.journal,
                    doi=r.doi,
                )
                exporter.write(ref)
    elif args.format == "json":
        data = [
            {
                "title": r.title,
                "authors": r.authors,
                "year": r.year,
                "journal": r.journal,
                "doi": r.doi,
                "pmid": r.pmid,
                "citation_count": r.citation_count,
                "url": r.url,
            }
            for r in results
        ]
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
    else:  # CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["title", "authors", "year", "journal", "doi", "pmid", "citation_count"],
            )
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "title": r.title,
                    "authors": "; ".join(r.authors),
                    "year": r.year,
                    "journal": r.journal,
                    "doi": r.doi,
                    "pmid": r.pmid,
                    "citation_count": r.citation_count,
                })

    logger.info("=" * 60)
    logger.info("Summary")
    logger.info(f"Results found: {len(results)}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Time: {elapsed}")
    logger.info("=" * 60)

    return 0


# =============================================================================
# RESOLVE COMMAND
# =============================================================================

def cmd_resolve(args: argparse.Namespace) -> int:
    """Resolve references to DOIs and metadata."""
    config = Config(
        email=args.mailto,
        input_file=Path(args.input),
        output_csv=Path(args.output),
        confidence_threshold=args.confidence,
    )

    setup_logging(verbose=args.verbose, log_file=Path("resolve.log"))

    if not config.input_file.exists():
        logger.error(f"Input file not found: {config.input_file}")
        return 1

    logger.info("=" * 60)
    logger.info("Reference Resolution")
    logger.info(f"Input: {config.input_file}")
    logger.info(f"Output: {config.output_csv}")
    logger.info("=" * 60)

    start = datetime.now()

    # Parse input
    parser = ReferenceParser()
    refs = parser.parse_file(config.input_file)
    logger.info(f"Found {len(refs)} references")

    # Resolve
    resolver = DOIResolver(config)
    stats = resolver.resolve_references(
        resume=args.resume,
        show_candidates=args.max_results,
    )

    elapsed = datetime.now() - start

    logger.info("=" * 60)
    logger.info("Summary")
    logger.info(f"Total: {stats['total']}")
    logger.info(f"Resolved: {stats['resolved']}")
    logger.info(f"Unresolved: {stats['unresolved']}")
    logger.info(f"Low confidence: {stats['low_confidence']}")
    logger.info(f"Time: {elapsed}")
    logger.info("=" * 60)

    return 0


# =============================================================================
# DOWNLOAD COMMAND
# =============================================================================

def cmd_download(args: argparse.Namespace) -> int:
    """Download open-access PDFs for resolved references."""
    config = Config(
        email=args.mailto,
        output_csv=Path(args.input_csv),
        download_dir=Path(args.download_dir),
        proxy_url=getattr(args, 'proxy', None),
        search_preprints=not getattr(args, 'no_preprints', False),
    )

    setup_logging(verbose=args.verbose, log_file=Path("download.log"))

    logger.info("=" * 60)
    logger.info("PDF Download")
    logger.info(f"Input CSV: {config.output_csv}")
    logger.info(f"Output dir: {config.download_dir}")
    logger.info("=" * 60)

    start = datetime.now()

    downloader = PDFDownloader(config)
    stats = downloader.run(
        input_csv=config.output_csv,
        output_dir=config.download_dir,
        resume=args.resume,
        update_csv=not args.no_update,
    )

    elapsed = datetime.now() - start

    logger.info("=" * 60)
    logger.info("Summary")
    logger.info(f"DOIs processed: {stats['total_dois']}")
    logger.info(f"Downloaded: {stats['downloaded']}")
    logger.info(f"No OA: {stats['no_oa']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Time: {elapsed}")
    logger.info("=" * 60)

    if stats["downloaded"] > 0:
        logger.info(f"\nPDFs saved to: {config.download_dir}")
        logger.info("Import into EndNote: File → Import → Folder... (PDF)")

    return 0


# =============================================================================
# PIPELINE COMMAND
# =============================================================================

def cmd_pipeline(args: argparse.Namespace) -> int:
    """Run full pipeline: parse → resolve → download."""
    config = Config(
        email=args.mailto,
        input_file=Path(args.input),
        output_csv=Path(args.output_csv),
        download_dir=Path(args.download_dir),
        confidence_threshold=args.confidence,
    )

    setup_logging(verbose=args.verbose, log_file=Path("pipeline.log"))

    if not config.input_file.exists():
        logger.error(f"Input file not found: {config.input_file}")
        return 1

    logger.info("=" * 60)
    logger.info("Full Pipeline: Parse → Resolve → Download")
    logger.info(f"Input: {config.input_file}")
    logger.info("=" * 60)

    start = datetime.now()

    # Step 1: Parse and resolve
    logger.info("\n### Step 1: Parsing and Resolving ###\n")
    parser = ReferenceParser()
    refs = parser.parse_file(config.input_file)
    logger.info(f"Found {len(refs)} references")

    resolver = DOIResolver(config)
    step1_stats = resolver.resolve_references(
        resume=args.resume,
        show_candidates=args.max_results,
    )

    if step1_stats["resolved"] == 0:
        logger.error("No references resolved. Aborting.")
        return 1

    # Step 2: Download PDFs
    logger.info("\n### Step 2: Downloading PDFs ###\n")
    downloader = PDFDownloader(config)
    step2_stats = downloader.run(
        input_csv=config.output_csv,
        output_dir=config.download_dir,
        resume=args.resume,
        update_csv=True,
    )

    # Step 3: Export to BibTeX if requested
    if args.bibtex:
        logger.info("\n### Step 3: Exporting BibTeX ###\n")
        # Re-read resolved refs and export
        with open(config.output_csv, "r", encoding="utf-8") as f:
            resolved_refs = list(csv.DictReader(f))

        with BibTeXExporter(config.output_bib) as exporter:
            for row in resolved_refs:
                if row.get(Columns.DOI):
                    ref = Reference(
                        citation=row.get(Columns.RAW_CITATION, ""),
                        title=row.get(Columns.TITLE, ""),
                        authors=row.get(Columns.AUTHORS, "").split("; "),
                        year=int(row[Columns.YEAR]) if row.get(Columns.YEAR) else None,
                        journal=row.get(Columns.JOURNAL, ""),
                        volume=row.get(Columns.VOLUME, ""),
                        pages=row.get(Columns.PAGES, ""),
                        doi=row.get(Columns.DOI, ""),
                    )
                    exporter.write(ref)
        logger.info(f"Exported to: {config.output_bib}")

    elapsed = datetime.now() - start

    logger.info("=" * 60)
    logger.info("Final Summary")
    logger.info(f"References: {step1_stats['total']}")
    logger.info(f"Resolved: {step1_stats['resolved']}")
    logger.info(f"PDFs downloaded: {step2_stats['downloaded']}")
    logger.info(f"Total time: {elapsed}")
    logger.info("=" * 60)

    return 0


# =============================================================================
# CONVERT COMMAND
# =============================================================================

def cmd_convert(args: argparse.Namespace) -> int:
    """Convert between reference formats."""
    setup_logging(verbose=args.verbose)

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Check if input is CSV (from resolve step)
    if input_path.suffix.lower() == ".csv":
        # Read from CSV
        refs = []
        with open(input_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ref = Reference(
                    citation=row.get(Columns.RAW_CITATION, ""),
                    title=row.get(Columns.TITLE, ""),
                    authors=row.get("authors", "").split("; ") if row.get("authors") else [],
                    year=int(row[Columns.YEAR]) if row.get(Columns.YEAR) and row[Columns.YEAR].isdigit() else None,
                    journal=row.get(Columns.JOURNAL, ""),
                    volume=row.get(Columns.VOLUME, ""),
                    issue=row.get("issue", ""),
                    pages=row.get(Columns.PAGES, ""),
                    doi=row.get(Columns.DOI, ""),
                )
                refs.append(ref)
    else:
        # Parse as reference file (bib, ris, txt)
        parser = ReferenceParser()
        refs = parser.parse_file(input_path)

    if args.format == "bibtex":
        with BibTeXExporter(output_path) as exporter:
            for ref in refs:
                exporter.write(ref)
    elif args.format == "json":
        with JSONExporter(output_path) as exporter:
            exporter.write_all(refs)
    else:  # CSV
        with CSVExporter(output_path) as exporter:
            for ref in refs:
                exporter.write(CSVExporter.ref_to_row(ref))

    logger.info(f"Converted {len(refs)} references to {args.format}")
    logger.info(f"Output: {output_path}")

    return 0


# =============================================================================
# CONTACTS COMMAND
# =============================================================================

def cmd_contacts(args: argparse.Namespace) -> int:
    """Extract author contacts and generate request emails."""
    config = Config(email=args.mailto)
    setup_logging(verbose=args.verbose)

    logger.info("=" * 60)
    logger.info("Author Contact Extraction")
    logger.info(f"Input: {args.input}")
    logger.info("=" * 60)

    extractor = AuthorContactExtractor(config)

    # Extract contacts
    input_csv = Path(args.input)
    contacts_by_doi = extractor.extract_from_csv(input_csv)

    logger.info(f"Found contacts for {len(contacts_by_doi)} papers")

    # Generate email requests
    output_file = Path(args.output) if args.output else Path("author_requests.txt")
    extractor.generate_request_emails(
        contacts_by_doi=contacts_by_doi,
        input_csv=input_csv,
        output_file=output_file,
    )

    logger.info(f"✓ Generated email requests: {output_file}")
    logger.info("\nTo use these requests:")
    logger.info("1. Review and customize each email")
    logger.info("2. Send manually or use your email client")
    logger.info("3. Be polite and respectful of authors' time")

    return 0


# =============================================================================
# RENAME COMMAND
# =============================================================================

def cmd_rename(args: argparse.Namespace) -> int:
    """Rename PDF files based on their metadata."""
    setup_logging(verbose=args.verbose)

    logger.info("=" * 60)
    logger.info("PDF Batch Renaming")
    logger.info(f"Input folder: {args.folder}")
    logger.info("=" * 60)

    folder = Path(args.folder)
    if not folder.exists():
        logger.error(f"Folder not found: {folder}")
        return 1

    renamer = PDFRenamer(dry_run=args.dry_run)

    # Rename PDFs
    output_dir = Path(args.output_dir) if args.output_dir else None
    results = renamer.rename_pdfs(
        folder=folder,
        pattern=args.pattern,
        output_dir=output_dir,
    )

    logger.info("\n" + "=" * 60)
    logger.info("Final Summary")
    logger.info(f"Successfully renamed: {len(results['renamed'])}")
    logger.info(f"Skipped (no metadata): {len(results['skipped'])}")
    logger.info(f"Failed: {len(results['failed'])}")
    logger.info("=" * 60)

    if output_dir:
        logger.info(f"\nRenamed/copied files saved to: {output_dir}")
    else:
        logger.info("\nFiles renamed in place")

    return 0


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="reftool",
        description="Reference Toolkit: discover, validate, resolve, download, and rename academic papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Search command ---
    search_p = subparsers.add_parser(
        "search",
        help="Search for papers (Google Scholar, PubMed, Crossref)",
    )
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("-o", "--output", default="search_results.csv", help="Output file")
    search_p.add_argument("--format", choices=["csv", "bibtex", "json"], default="csv")
    search_p.add_argument("--source", choices=["all", "scholar", "pubmed", "crossref"], default="all")
    search_p.add_argument("--limit", type=int, default=50)
    search_p.add_argument("--year-start", type=int)
    search_p.add_argument("--year-end", type=int)
    search_p.add_argument("--mailto", default="benzoic@gmail.com")
    search_p.add_argument("-v", "--verbose", action="store_true")
    search_p.set_defaults(func=cmd_search)

    # --- Resolve command ---
    resolve_p = subparsers.add_parser(
        "resolve",
        help="Resolve references to DOIs",
        aliases=["dois"],
    )
    resolve_p.add_argument("input", help="Input file (txt, bib, ris)")
    resolve_p.add_argument("-o", "--output", default="resolved_refs.csv")
    resolve_p.add_argument("--mailto", default="benzoic@gmail.com")
    resolve_p.add_argument("--confidence", type=float, default=60.0)
    resolve_p.add_argument("--resume", action="store_true")
    resolve_p.add_argument("--max-results", type=int, default=1)
    resolve_p.add_argument("-v", "--verbose", action="store_true")
    resolve_p.set_defaults(func=cmd_resolve)

    # --- Download command ---
    download_p = subparsers.add_parser(
        "download",
        help="Download open-access PDFs",
        aliases=["pdfs"],
    )
    download_p.add_argument("input_csv", help="CSV from resolve step")
    download_p.add_argument("--download-dir", default="pdfs")
    download_p.add_argument("--mailto", default="benzoic@gmail.com")
    download_p.add_argument("--resume", action="store_true")
    download_p.add_argument("--no-update", action="store_true", help="Don't update CSV")
    download_p.add_argument("--proxy", help="Proxy URL for institutional access")
    download_p.add_argument("--no-preprints", action="store_true", help="Disable preprint search")
    download_p.add_argument("--no-semantic-scholar", action="store_true", help="Disable Semantic Scholar search")
    download_p.add_argument("--no-quality-check", action="store_true", help="Disable PDF quality validation")
    download_p.add_argument("-v", "--verbose", action="store_true")
    download_p.set_defaults(func=cmd_download)

    # --- Pipeline command ---
    pipeline_p = subparsers.add_parser(
        "pipeline",
        help="Run full pipeline (resolve + download)",
    )
    pipeline_p.add_argument("input", help="Input file (txt, bib, ris)")
    pipeline_p.add_argument("--output-csv", default="resolved_refs.csv")
    pipeline_p.add_argument("--download-dir", default="pdfs")
    pipeline_p.add_argument("--bibtex", action="store_true", help="Also export BibTeX")
    pipeline_p.add_argument("--mailto", default="benzoic@gmail.com")
    pipeline_p.add_argument("--confidence", type=float, default=60.0)
    pipeline_p.add_argument("--resume", action="store_true")
    pipeline_p.add_argument("--max-results", type=int, default=1)
    pipeline_p.add_argument("-v", "--verbose", action="store_true")
    pipeline_p.set_defaults(func=cmd_pipeline)

    # --- Convert command ---
    convert_p = subparsers.add_parser(
        "convert",
        help="Convert between reference formats",
    )
    convert_p.add_argument("input", help="Input file")
    convert_p.add_argument("-o", "--output", required=True, help="Output file")
    convert_p.add_argument("--format", choices=["bibtex", "csv", "json"], default="bibtex")
    convert_p.add_argument("-v", "--verbose", action="store_true")
    convert_p.set_defaults(func=cmd_convert)

    # --- Contacts command ---
    contacts_p = subparsers.add_parser(
        "contacts",
        help="Extract author contacts and generate request emails",
    )
    contacts_p.add_argument("input", help="Input CSV file")
    contacts_p.add_argument("-o", "--output", default="author_requests.txt", help="Output file")
    contacts_p.add_argument("--mailto", default="benzoic@gmail.com")
    contacts_p.add_argument("-v", "--verbose", action="store_true")
    contacts_p.set_defaults(func=cmd_contacts)

    # --- Rename command ---
    rename_p = subparsers.add_parser(
        "rename",
        help="Rename PDF files using their metadata",
        aliases=["pdf-rename"],
    )
    rename_p.add_argument("folder", help="Folder containing PDF files to rename")
    rename_p.add_argument("--pattern", default="{title}_{year}",
                       help="Naming pattern (default: {title}_{year})")
    rename_p.add_argument("--output-dir", help="Copy renamed files to this directory instead of renaming in place")
    rename_p.add_argument("--dry-run", action="store_true",
                       help="Show what would be renamed without actually doing it")
    rename_p.add_argument("-v", "--verbose", action="store_true")
    rename_p.set_defaults(func=cmd_rename)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
