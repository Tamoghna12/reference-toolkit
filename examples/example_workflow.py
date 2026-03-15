#!/usr/bin/env python3
"""
Example workflow demonstrating Reference Toolkit usage.

This script shows how to:
1. Search for papers
2. Resolve references to DOIs
3. Download PDFs
4. Rename PDFs using metadata
"""

from pathlib import Path
from reference_toolkit.search import SearchEngine
from reference_toolkit.config import Config
from reference_toolkit.doi_resolver import DOIResolver
from reference_toolkit.pdf_downloader import PDFDownloader
from reference_toolkit.pdf_renamer import PDFRenamer


def main():
    """Run example workflow."""
    # Configuration
    config = Config(
        email="your@email.com",  # Replace with your email
        search_limit=10,
        output_csv=Path("results/resolved.csv"),
        download_dir=Path("results/pdfs"),
    )

    # Create output directory
    config.download_dir.mkdir(parents=True, exist_ok=True)
    config.output_csv.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Reference Toolkit Example Workflow")
    print("=" * 60)

    # Step 1: Search for papers
    print("\n1. Searching for papers...")
    search_engine = SearchEngine(config)
    query = "machine learning protein folding"
    print(f"   Query: {query}")

    results = search_engine.search(
        query=query,
        limit=5,
    )
    print(f"   Found: {len(results)} papers")

    # Step 2: Resolve references (if you have a reference file)
    print("\n2. Resolving references...")
    print("   (Skip this step if you don't have a reference file)")
    # Uncomment if you have a reference file:
    # resolver = DOIResolver(config)
    # stats = resolver.resolve_references(resume=True)
    # print(f"   Resolved: {stats['resolved']}/{stats['total']}")

    # Step 3: Download PDFs
    print("\n3. Downloading PDFs...")
    print("   (Skip this step if you don't have a resolved CSV)")
    # Uncomment if you have a resolved CSV:
    # downloader = PDFDownloader(config)
    # stats = downloader.run(
    #     input_csv=config.output_csv,
    #     output_dir=config.download_dir,
    #     resume=True,
    # )
    # print(f"   Downloaded: {stats['downloaded']}/{stats['total_dois']}")

    # Step 4: Rename PDFs
    print("\n4. Renaming PDFs...")
    if config.download_dir.exists():
        renamer = PDFRenamer(dry_run=True)  # Set dry_run=False to actually rename
        results = renamer.rename_pdfs(
            folder=config.download_dir,
            output_dir=config.download_dir / "renamed",
        )
        print(f"   Would rename: {len(results['renamed'])} PDFs")
        print(f"   Set dry_run=False to actually rename files")
    else:
        print("   No PDFs found to rename")

    print("\n" + "=" * 60)
    print("Workflow complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
