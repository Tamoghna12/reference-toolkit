"""DOI resolution functionality using Crossref."""

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from reference_toolkit.config import Config, Columns
from reference_toolkit.parser import ReferenceParser
from reference_toolkit.crossref import CrossrefClient, CrossrefResult

logger = logging.getLogger(__name__)


@dataclass
class ResolutionStats:
    """Statistics for resolution process."""

    total: int = 0
    resolved: int = 0
    unresolved: int = 0
    low_confidence: int = 0
    skipped: int = 0


class DOIResolver:
    """Resolve EndNote references to DOIs using Crossref."""

    def __init__(self, config: Config):
        self.config = config
        self.parser = ReferenceParser()
        self.crossref = CrossrefClient(config)

    def _load_processed(self) -> set[str]:
        """Load already-processed citations (for resume)."""
        processed = set()
        if not self.config.output_csv.exists():
            return processed

        with open(self.config.output_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                citation = row.get(Columns.RAW_CITATION, "")
                if citation:
                    processed.add(citation)

        return processed

    def resolve_references(
        self,
        input_file: Optional[Path] = None,
        output_csv: Optional[Path] = None,
        resume: bool = False,
        show_candidates: int = 0,
        confidence_threshold: Optional[float] = None,
    ) -> dict:
        """Resolve all references to DOIs.

        Args:
            input_file: Override input file
            output_csv: Override output CSV
            resume: Skip already-processed references
            show_candidates: Show top N candidates for each reference
            confidence_threshold: Override confidence threshold

        Returns:
            Statistics dict
        """
        stats = {
            "total": 0,
            "resolved": 0,
            "unresolved": 0,
            "low_confidence": 0,
            "skipped": 0,
        }

        input_path = input_file or self.config.input_file
        output_path = output_csv or self.config.output_csv
        threshold = confidence_threshold or self.config.confidence_threshold

        refs = list(self.parser.iter_references(input_path))
        stats["total"] = len(refs)
        logger.info(f"Found {len(refs)} references")

        processed = self._load_processed() if resume else set()
        if processed:
            logger.info(f"Resuming: {len(processed)} already processed")

        # Prepare output files
        file_mode = "a" if resume and processed else "w"
        write_header = not (resume and processed and output_path.exists())

        main_fields = [
            Columns.RAW_CITATION,
            Columns.TITLE,
            Columns.DOI,
            Columns.CROSSREF_SCORE,
            Columns.MATCH_TYPE,
            Columns.CONFIDENCE_FLAG,
            Columns.STATUS,
        ]

        unresolved_fields = [Columns.RAW_CITATION, "reason"]

        low_conf_fields = [
            Columns.RAW_CITATION,
            Columns.TITLE,
            Columns.DOI,
            Columns.CROSSREF_SCORE,
            Columns.MATCH_TYPE,
        ]

        with (
            open(output_path, file_mode, encoding="utf-8", newline="") as main_f,
            open(
                self.config.unresolved_csv, "w", encoding="utf-8", newline=""
            ) as unres_f,
            open(
                self.config.low_confidence_csv, "w", encoding="utf-8", newline=""
            ) as low_f,
        ):
            main_writer = csv.DictWriter(main_f, fieldnames=main_fields)
            unres_writer = csv.DictWriter(unres_f, fieldnames=unresolved_fields)
            low_writer = csv.DictWriter(low_f, fieldnames=low_conf_fields)

            if write_header:
                main_writer.writeheader()
                unres_writer.writeheader()
                low_writer.writeheader()

            for i, ref in enumerate(refs, 1):
                logger.info(f"[{i}/{len(refs)}] {ref.citation[:50]}...")

                if ref.citation in processed:
                    logger.info("  Skipping (already processed)")
                    stats["skipped"] += 1
                    continue

                result = self.crossref.lookup(ref.citation)

                if result:
                    flag = (
                        "low"
                        if result.score < threshold
                        else "ok"
                    )

                    main_writer.writerow({
                        Columns.RAW_CITATION: ref.citation,
                        Columns.TITLE: result.title,
                        Columns.DOI: result.doi,
                        Columns.CROSSREF_SCORE: result.score,
                        Columns.MATCH_TYPE: result.match_type,
                        Columns.CONFIDENCE_FLAG: flag,
                        Columns.STATUS: "resolved",
                    })
                    main_f.flush()
                    stats["resolved"] += 1
                    logger.info(
                        f"  DOI: {result.doi} (score: {result.score:.1f}, {flag})"
                    )

                    if flag == "low":
                        low_writer.writerow({
                            Columns.RAW_CITATION: ref.citation,
                            Columns.TITLE: result.title,
                            Columns.DOI: result.doi,
                            Columns.CROSSREF_SCORE: result.score,
                            Columns.MATCH_TYPE: result.match_type,
                        })
                        low_f.flush()
                        stats["low_confidence"] += 1

                    # Show candidates if requested
                    if show_candidates > 1:
                        candidates = self.crossref.get_candidates(
                            ref.citation, show_candidates
                        )
                        if candidates:
                            logger.info(f"  Top {len(candidates)} candidates:")
                            for j, c in enumerate(candidates, 1):
                                logger.info(
                                    f"    {j}. [{c['score']:.1f}] {c['title'][:40]}... "
                                    f"({c['journal']}) {c['doi']}"
                                )
                else:
                    main_writer.writerow({
                        Columns.RAW_CITATION: ref.citation,
                        Columns.TITLE: "",
                        Columns.DOI: "",
                        Columns.CROSSREF_SCORE: 0,
                        Columns.MATCH_TYPE: "none",
                        Columns.CONFIDENCE_FLAG: "none",
                        Columns.STATUS: "unresolved",
                    })
                    main_f.flush()

                    unres_writer.writerow({
                        Columns.RAW_CITATION: ref.citation,
                        "reason": "no_crossref_match",
                    })
                    unres_f.flush()

                    stats["unresolved"] += 1
                    logger.warning("  No match found")

        return stats
