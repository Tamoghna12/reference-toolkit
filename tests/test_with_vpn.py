#!/usr/bin/env python3
"""Test PDF download while connected to Loughborough University VPN.

Before running this script:
1. Connect to vpn.lboro.ac.uk using your VPN client
2. Verify connection with: curl ipinfo.io
3. Then run this script
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from reference_toolkit.config import Config
from reference_toolkit.pdf_downloader import PDFDownloader

def check_vpn_connection():
    """Check if we're connected through VPN."""
    import socket
    import requests

    print("Checking VPN connection...")

    try:
        # Get public IP
        response = requests.get('https://ipinfo.io/json', timeout=5)
        data = response.json()

        ip = data.get('ip', 'Unknown')
        org = data.get('org', 'Unknown')

        print(f"  Your IP: {ip}")
        print(f"  Organization: {org}")

        # Check if it's Loughborough
        if 'loughborough' in org.lower() or 'lboro' in org.lower():
            print("  ✓ Connected to Loughborough University network!")
            return True
        else:
            print("  ⚠ Not connected to Loughborough VPN")
            print(f"  Current network: {org}")
            return False

    except Exception as e:
        print(f"  ✗ Could not check connection: {e}")
        return None

def test_papers_with_vpn():
    """Test downloading papers that previously failed."""

    print("\n" + "=" * 60)
    print("TESTING PDF DOWNLOAD WITH Loughborough VPN")
    print("=" * 60)

    # Check VPN first
    vpn_status = check_vpn_connection()

    if vpn_status is False:
        print("\n⚠ WARNING: Not connected to Loughborough VPN!")
        print("\nPlease connect to vpn.lboro.ac.uk first:")
        print("  1. Open Cisco AnyConnect (or your VPN client)")
        print("  2. Connect to: vpn.lboro.ac.uk")
        print("  3. Enter your university username and password")
        print("  4. Run this script again")
        print("\nAttempting download anyway (may fail)...")

    # Configure downloader
    config = Config(
        email="benzoic@gmail.com",
        download_dir=Path("vpn_test_output"),
    )

    downloader = PDFDownloader(config)

    # Test papers that previously failed with 403 errors
    test_papers = [
        {
            "doi": "10.3390/w14203210",
            "title": "Assessment of Artificial Sweeteners as Wastewater Contaminants",
            "authors": "Various",
            "year": "2022",
            "publisher": "MDPI",
            "previous_error": "403 Forbidden",
        },
        {
            "doi": "10.3390/nu15051260",
            "title": "Sweetener System Intervention Shifted Neutrophils",
            "authors": "Various",
            "year": "2023",
            "publisher": "MDPI",
            "previous_error": "403 Forbidden",
        },
    ]

    print("\nTesting papers that previously failed:\n")

    results = []

    for i, paper in enumerate(test_papers, 1):
        print(f"[{i}/{len(test_papers)}] {paper['title'][:50]}...")
        print(f"  DOI: {paper['doi']}")
        print(f"  Publisher: {paper['publisher']}")
        print(f"  Previous error: {paper['previous_error']}")

        result = downloader.download_single(
            doi=paper['doi'],
            title=paper['title'],
            authors=paper['authors'],
            year=paper['year'],
        )

        if result.success:
            print(f"  ✓ SUCCESS with VPN!")
            print(f"    Saved: {result.output_path.name}")
            print(f"    Size: {result.output_path.stat().st_size / 1024:.1f} KB")
            results.append(("SUCCESS", paper['doi']))
        else:
            print(f"  ✗ Still failed: {result.error}")
            results.append(("FAILED", paper['doi']))

        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    successful = sum(1 for r, _ in results if r == "SUCCESS")
    total = len(results)

    print(f"Successfully downloaded: {successful}/{total}")

    if successful > 0:
        print("\n✓ VPN is working! You can now run bulk downloads:")
        print("  reftool download resolved_refs.csv --download-dir pdfs_with_vpn")
    elif successful == 0 and vpn_status:
        print("\n⚠ VPN is connected but downloads still failed.")
        print("  This might mean:")
        print("  - Publisher blocks institutional access")
        print("  - Paper requires individual subscription")
        print("  - Try a different paper")
    else:
        print("\n⚠ Please connect to VPN first")

    print("\nPDFs saved to: vpn_test_output/")
    print("=" * 60)

if __name__ == "__main__":
    test_papers_with_vpn()
