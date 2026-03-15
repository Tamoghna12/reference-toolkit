#!/usr/bin/env python3
"""Test proxy configuration with a single paper download."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from reference_toolkit.config import Config
from reference_toolkit.pdf_downloader import PDFDownloader

def test_proxy_download(
    doi: str,
    proxy_url: str = None,
    output_dir: str = "test_proxy_output"
):
    """Test downloading a single paper with proxy.

    Args:
        doi: DOI to test
        proxy_url: Optional proxy URL (e.g., "http://proxy.university.edu:3128")
        output_dir: Where to save the test PDF
    """

    # Configure with proxy if provided
    config = Config(
        email="benzoic@gmail.com",
        download_dir=Path(output_dir),
        proxy_url=proxy_url,
    )

    print("=" * 60)
    print("PROXY DOWNLOAD TEST")
    print("=" * 60)
    print(f"DOI: {doi}")
    print(f"Proxy: {proxy_url or 'None (direct connection)'}")
    print(f"Output: {output_dir}")
    print("=" * 60)

    # Create downloader
    downloader = PDFDownloader(config)

    # Test with a paper that failed before (MDPI paper)
    # DOI: 10.3390/w14203210 - "Assessment of Artificial Sweeteners as Wastewater..."
    title = "Assessment of Artificial Sweeteners as Wastewater Contaminants"
    authors = "Author Unknown"
    year = "2022"

    print(f"\nTesting download of:")
    print(f"  Title: {title}")
    print(f"  DOI: {doi}")
    print()

    # Attempt download
    result = downloader.download_single(
        doi=doi,
        title=title,
        authors=authors,
        year=year,
    )

    # Report results
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    if result.success:
        print(f"✓ SUCCESS!")
        print(f"  Saved to: {result.output_path}")
        print(f"  PDF URL: {result.pdf_url}")
        print(f"  OA Status: {result.oa_status}")
        print(f"\nFile size: {result.output_path.stat().st_size / 1024:.1f} KB")
        return 0
    else:
        print(f"✗ FAILED")
        print(f"  Error: {result.error}")
        print(f"  OA Status: {result.oa_status}")

        # Give specific advice based on error
        if result.error == "download_failed":
            print("\nPossible issues:")
            print("  1. Proxy authentication required")
            print("  2. Proxy URL incorrect")
            print("  3. Firewall blocking connection")
            print("  4. Publisher still blocking access")
        elif result.error == "no_oa_pdf":
            print("\nThis paper is not open access even with proxy.")

        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test proxy configuration for PDF downloads"
    )
    parser.add_argument(
        "--doi",
        default="10.3390/w14203210",
        help="DOI to test (default: MDPI paper that failed before)"
    )
    parser.add_argument(
        "--proxy",
        help="Proxy URL (e.g., http://proxy.university.edu:3128 or http://user:pass@proxy:3128)"
    )
    parser.add_argument(
        "--output-dir",
        default="test_proxy_output",
        help="Output directory for test download"
    )

    args = parser.parse_args()

    sys.exit(test_proxy_download(
        doi=args.doi,
        proxy_url=args.proxy,
        output_dir=args.output_dir
    ))
