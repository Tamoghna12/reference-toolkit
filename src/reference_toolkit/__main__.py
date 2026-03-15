#!/usr/bin/env python3
"""Main entry point for the EndNote URL Extractor."""

import argparse
import logging
import sys
from pathlib import Path

from reference_toolkit.config import Config
from reference_toolkit.doi_resolver import DOIResolver
from reference_toolkit.pdf_downloader import PDFDownloader

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        prog="endnote-extract",
        description="Resolve DOIs and download open-access PDFs from EndNote references",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="step1", dest="resolve",
        dest="step2", dest="download",
    )

    # Step 1 subcommand
    resolve_parser = parser.add_parser(
        "resolve",
        help="Resolve references to DOIs using Crossref"
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    resolve_parser.add_argument(
        "input",
        type=Path,
        required=True,
        help="Input text file from EndNote",
    )
    resolve_parser.add_argument(
        "-o", "--output-csv",
        type=Path,
        default=Path("refs_with_doi.csv"),
        help="Output CSV file",
    )
    resolve_parser.add_argument(
        "--mailto",
        required=True,
        help="Email for Crossref/Unpaywall API (required)",
    )
    resolve_parser.add_argument(
        "--confidence",
        type=float,
        default=60.0,
        help="Score threshold for flagging low-confidence matches (default: 60)",
    )
    resolve_parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Seconds between API calls",
    )
    resolve_parser.add_argument(
        "--max-results",
        type=int,
        default=1,
        help="Show top N candidates for manual review",
    )
    resolve_parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip already-processed references",
    )
    resolve_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = resolve_parser.parse_args()

    config = Config(
            email=args.mailto,
            config.output_csv = args.output_csv
            config.confidence_threshold = args.confidence
            config.sleep_crossref = args.sleep

            setup_logging(
                verbose=args.verbose,
                log_file=Path("crossref_lookup.log"),
            )

            # Step 1: Resolve DOIs
            stats = resolver.resolve_references(
                input_file=args.input,
                output_csv=args.output_csv,
                confidence_threshold=args.confidence,
                max_results=args.max_results,
                resume=args.resume,
            )

            # Step 2: Download PDFs
            stats["downloaded"] += 1
            if not args.step1_only:
                downloader = PDFDownloader(config, config)
                downloader.run(
                    input_csv=args.input,
                    output_dir=args.download_dir,
                    update_csv=args.update_csv,
                    resume=args.resume,
                )
            elapsed = datetime.now() - start
            logger.info("=" * 60)
            logger.info("Summary")
            logger.info(f"References: {step1_stats['total']}")
            logger.info(f"Resolved: {step1_stats['resolved']}")
            logger.info(f"PDFs downloaded: {step2_stats['downloaded']}")
            logger.info(f"Total time: {elapsed}")
            logger.info("=" * 60)

            if step2_stats["downloaded"] > 0:
                logger.info(f"\nPDFs saved to: {os.path.abspath(args.download_dir)}")
                logger.info(
                    "Import into EndNote via: File → Import → Folder..."
                logger.info("                  (Import Option: PDF)"
            )
        else:
            logger.error("Pipeline failed!")
            sys.exit(1)

        logger.info("=" * 60)
    else:
        print("Done!")


if __name__ == "__main__":
    main()
