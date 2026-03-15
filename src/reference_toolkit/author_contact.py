"""Author contact extraction for requesting PDF copies."""

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from reference_toolkit.config import Config

logger = logging.getLogger(__name__)


@dataclass
class AuthorContact:
    """Contact information for a paper author."""

    name: str
    email: Optional[str] = None
    is_corresponding: bool = False
    affiliation: Optional[str] = None


class AuthorContactExtractor:
    """Extract author contact information from papers."""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

    def extract_from_csv(self, input_csv: Path) -> dict[str, list[AuthorContact]]:
        """Extract author contacts from a CSV of papers.

        Args:
            input_csv: CSV with paper metadata

        Returns:
            Dict mapping DOI to list of author contacts
        """
        contacts_by_doi = {}

        if not input_csv.exists():
            logger.error(f"CSV not found: {input_csv}")
            return contacts_by_doi

        with open(input_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                doi = row.get("doi", "").strip()
                title = row.get("title", "").strip()
                authors = row.get("authors", "").strip()

                if not doi:
                    continue

                # Parse author string to extract emails
                contacts = self._parse_author_string(authors)
                contacts_by_doi[doi] = contacts

                # If no emails found, try publisher page
                if not any(c.email for c in contacts):
                    logger.info(f"  No emails in author string, checking publisher page...")
                    contacts = self.extract_from_publisher(doi, title)
                    contacts_by_doi[doi] = contacts

        return contacts_by_doi

    def _parse_author_string(self, authors: str) -> list[AuthorContact]:
        """Parse author string to extract email addresses.

        Args:
            authors: Semicolon-separated author string

        Returns:
            List of AuthorContact objects
        """
        contacts = []

        if not authors:
            return contacts

        # Split by semicolon
        author_list = authors.split(';')

        for i, author in enumerate(author_list):
            author = author.strip()
            if not author:
                continue

            # Extract email using regex
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', author)
            email = email_match.group(0) if email_match else None

            # Extract name (remove email if present)
            name = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '', author).strip()
            name = re.sub(r'[<>\[\](){}]', '', name).strip()

            # First author is often corresponding
            is_corresponding = (i == 0) or ('corresponding' in author.lower())

            contacts.append(AuthorContact(
                name=name,
                email=email,
                is_corresponding=is_corresponding,
            ))

        return contacts

    def extract_from_publisher(self, doi: str, title: str) -> list[AuthorContact]:
        """Try to extract author contacts from publisher page.

        Args:
            doi: Paper DOI
            title: Paper title

        Returns:
            List of AuthorContact objects
        """
        # Try to get publisher page from DOI
        doi_url = f"https://doi.org/{doi}"

        try:
            response = self.session.get(
                doi_url,
                timeout=self.config.request_timeout,
                allow_redirects=True
            )

            if response.status_code != 200:
                return []

            # Extract emails from HTML
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', response.text)
            unique_emails = list(set(emails))

            contacts = []
            for email in unique_emails[:5]:  # Limit to first 5
                contacts.append(AuthorContact(
                    name="",
                    email=email,
                    is_corresponding=True,
                ))

            return contacts

        except Exception as e:
            logger.debug(f"Failed to extract from publisher: {e}")
            return []

    def generate_request_emails(
        self,
        contacts_by_doi: dict[str, list[AuthorContact]],
        input_csv: Path,
        output_file: Optional[Path] = None,
    ) -> Path:
        """Generate email request templates for authors.

        Args:
            contacts_by_doi: Dict mapping DOI to author contacts
            input_csv: Original CSV with paper metadata
            output_file: Where to save email templates

        Returns:
            Path to generated email file
        """
        if output_file is None:
            output_file = Path("author_requests.txt")

        # Read paper metadata
        papers = {}
        with open(input_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                doi = row.get("doi", "").strip()
                if doi:
                    papers[doi] = row

        # Generate email requests
        with open(output_file, "w", encoding="utf-8") as f:
            for doi, contacts in contacts_by_doi.items():
                if doi not in papers:
                    continue

                paper = papers[doi]
                title = paper.get("title", "").strip()

                # Find corresponding author with email
                corresponding = None
                for contact in contacts:
                    if contact.email and contact.is_corresponding:
                        corresponding = contact
                        break

                # If no corresponding, use first with email
                if not corresponding:
                    for contact in contacts:
                        if contact.email:
                            corresponding = contact
                            break

                if not corresponding:
                    continue

                # Generate email
                email_text = self._generate_email_template(
                    title=title,
                    doi=doi,
                    author_name=corresponding.name,
                    author_email=corresponding.email,
                )

                f.write(email_text)
                f.write("\n" + "=" * 80 + "\n\n")

        logger.info(f"Generated {len(contacts_by_doi)} email requests in {output_file}")
        return output_file

    def _generate_email_template(
        self,
        title: str,
        doi: str,
        author_name: str,
        author_email: str,
    ) -> str:
        """Generate a polite email requesting a PDF copy.

        Args:
            title: Paper title
            doi: Paper DOI
            author_name: Recipient name
            author_email: Recipient email

        Returns:
            Email text
        """
        template = f"""To: {author_email}
Subject: PDF Request: {title[:70]}...

Dear {author_name if author_name else 'Colleague'},

I hope this email finds you well. I am currently conducting research on a related topic and would greatly appreciate a PDF copy of your paper:

"{title}"

DOI: {doi}

I am particularly interested in this work because it relates to my current research on [YOUR TOPIC]. If you are able to share a copy, I would be very grateful.

Thank you for your time and consideration.

Best regards,
[Your Name]
[Your Institution]
[Your Email]

---
This request was generated automatically by the Reference Toolkit.
If you believe this is an error, please disregard.
"""

        return template


def generate_request_script(
    contacts_csv: Path,
    output_script: Path = Path("send_requests.sh"),
) -> Path:
    """Generate a shell script to send email requests.

    Args:
        contacts_csv: CSV with author contacts
        output_script: Where to save the script

    Returns:
        Path to generated script
    """
    script_content = """#!/bin/bash
# Auto-generated script to send PDF requests to authors
# WARNING: Review all emails before sending!
# Edit this script to customize messages before running.

set -e

echo "=== PDF Request Email Sender ==="
echo "This script will send emails to authors requesting PDF copies."
echo "Please review all emails before sending!"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "Sending emails..."
# Add your email sending logic here
# For example, using mailx or sendmail

# Example:
# cat email_template.txt | mailx -s "PDF Request" author@example.com

echo "Done!"
"""

    with open(output_script, "w") as f:
        f.write(script_content)

    # Make executable
    output_script.chmod(0o755)

    logger.info(f"Generated email script: {output_script}")
    return output_script
