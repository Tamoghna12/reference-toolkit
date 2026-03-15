# Enhanced Features for Reference Toolkit

## Priority 1: Better Preprint Handling

### Current Issues:
- arXiv rate limits after 3 requests (429 errors)
- bioRxiv blocks automated access (403 errors)
- Limited to 3 preprint servers
- Basic title matching (50% overlap)

### Solutions:

#### 1. Rate Limit Handling
```python
# Add exponential backoff and caching
import time
from functools import lru_cache
from collections import defaultdict

class PreprintClient:
    def __init__(self, config: Config):
        self.config = config
        self.request_times = defaultdict(list)  # Track requests per domain
        self.cache = {}  # Simple cache

    def _rate_limit_wait(self, domain: str):
        """Implement exponential backoff for rate limits."""
        now = time.time()

        # Remove old request times (>1 hour ago)
        self.request_times[domain] = [
            t for t in self.request_times[domain]
            if now - t < 3600
        ]

        # If too many requests, wait
        if len(self.request_times[domain]) > 10:
            wait_time = min(2 ** len(self.request_times[domain]), 60)
            logger.info(f"Rate limit detected, waiting {wait_time}s...")
            time.sleep(wait_time)

        self.request_times[domain].append(now)

    @lru_cache(maxsize=1000)
    def search_arxiv_cached(self, title: str):
        """Cached arXiv search to avoid duplicate requests."""
        return self.search_arxiv(title)
```

#### 2. More Preprint Servers
```python
class PreprintClient:
    def search_all_extended(self, title: str, doi: str) -> Optional[str]:
        """Search extended list of preprint servers."""

        servers = [
            ("arXiv", self.search_arxiv),
            ("bioRxiv", self.search_biorxiv),
            ("medRxiv", self.search_medrxiv),
            ("PMC", self.search_pmc),
            # NEW SERVERS:
            ("ChemRxiv", self.search_chemrxiv),
            ("SSRN", self.search_ssrn),
            ("RePEc", self.search_repec),
            ("ResearchSquare", self.search_researchsquare),
            ("Preprints.org", self.search_preprints_org),
            ("arXiv Vanity", self.search_arxiv_vanity),
            ("Edelweiss", self.search_edelweiss),
            ("F1000Research", self.search_f1000),
        ]

        for server_name, search_func in servers:
            try:
                logger.info(f"Searching {server_name}...")
                url = search_func(title)
                if url:
                    logger.info(f"✓ Found on {server_name}")
                    return url
            except Exception as e:
                logger.debug(f"{server_name} search failed: {e}")

        return None
```

#### 3. Better Title Matching
```python
from difflib import SequenceMatcher
import re

class TitleMatcher:
    """Advanced title matching for preprint finding."""

    def match_titles(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles."""
        # Normalize both titles
        t1 = self._normalize_title(title1)
        t2 = self._normalize_title(title2)

        # Use SequenceMatcher for better similarity
        similarity = SequenceMatcher(None, t1, t2).ratio()

        # Bonus for word overlap
        words1 = set(t1.split())
        words2 = set(t2.split())
        word_overlap = len(words1 & words2) / max(len(words1), len(words2))

        # Combined score
        return (similarity * 0.6) + (word_overlap * 0.4)

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        # Lowercase
        title = title.lower()
        # Remove punctuation
        title = re.sub(r'[^\w\s]', ' ', title)
        # Remove common words
        stopwords = {'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        words = [w for w in title.split() if w not in stopwords]
        return ' '.join(words)
```

---

## Priority 2: Alternative PDF Sources

### 1. Semantic Scholar Integration
```python
class SemanticScholarClient:
    """Search Semantic Scholar for PDFs and metadata."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def search_paper(self, title: str, doi: str) -> Optional[dict]:
        """Search for paper metadata and open access links."""

        # Try DOI first
        if doi:
            url = f"{self.BASE_URL}/paper/DOI:{doi}"
            response = self.session.get(url, params={'fields': 'openAccessPdf'})
            if response.status_code == 200:
                data = response.json()
                if data.get('openAccessPdf'):
                    return data

        # Try title search
        query = quote(title)
        url = f"{self.BASE_URL}/paper/search"
        params = {
            'query': title,
            'limit': 5,
            'fields': 'paperId,title,authors,year,openAccessPdf'
        }

        response = self.session.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            for paper in data.get('data', []):
                # Find best match using title similarity
                if self.match_titles(title, paper['title']) > 0.7:
                    if paper.get('openAccessPdf'):
                        return paper

        return None
```

### 2. Google Scholar PDF Search
```python
class ScholarPDFSearcher:
    """Search Google Scholar for direct PDF links."""

    def search_pdf(self, title: str, authors: str) -> Optional[str]:
        """Search Scholar for [PDF] links."""

        query = f"{title} {authors}"
        search_url = f"https://scholar.google.com/scholar?q={quote(query)}"

        try:
            response = self.session.get(
                search_url,
                headers={'User-Agent': 'Mozilla/5.0...'},
                timeout=10
            )

            # Parse HTML for [PDF] links
            import re
            pdf_links = re.findall(
                r'href="([^"]*\[PDF\][^"]*)"',
                response.text
            )

            # Extract actual URLs
            urls = re.findall(
                r'url=([^"]+)',
                pdf_links[0] if pdf_links else ''
            )

            if urls:
                return urls[0]

        except Exception as e:
            logger.debug(f"Scholar search failed: {e}")

        return None
```

### 3. CORE Aggregator
```python
class COREClient:
    """Search CORE (aggregator of open access papers)."""

    def search(self, title: str, doi: str) -> Optional[str]:
        """Search CORE for OA version."""

        api_key = self.config.core_api_key  # Get free key from core.ac.uk

        if doi:
            # Search by DOI
            url = f"https://api.core.ac.uk/v3/articles/doi/{doi}"
            params = {'apiKey': api_key}

            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('downloadUrl'):
                    return data['downloadUrl']

        # Search by title
        url = "https://api.core.ac.uk/v3/search/works"
        params = {
            'apiKey': api_key,
            'q': title,
            'limit': 1
        }

        response = self.session.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                return results[0].get('downloadUrl')

        return None
```

---

## Priority 3: Enhanced Metadata & Quality

### 1. PDF Quality Validation
```python
class PDFQualityChecker:
    """Validate PDF quality and detect issues."""

    def check_pdf(self, pdf_path: Path) -> dict:
        """Check PDF for common issues."""

        issues = []
        score = 100

        # Check file size
        size = pdf_path.stat().st_size
        if size < 10000:  # < 10KB
            issues.append("Very small file (likely corrupted)")
            score -= 50
        elif size > 100_000_000:  # > 100MB
            issues.append("Very large file (may be scanned)")
            score -= 10

        # Check if PDF is encrypted
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if reader.is_encrypted:
                    issues.append("PDF is encrypted (password protected)")
                    score -= 30

                # Check page count
                pages = len(reader.pages)
                if pages == 0:
                    issues.append("No pages (corrupted)")
                    score -= 50
                elif pages < 3:
                    issues.append(f"Only {pages} page(s) (may be partial)")
                    score -= 20

                # Check for text content
                text_content = False
                for page in reader.pages[:3]:  # Check first 3 pages
                    text = page.extract_text()
                    if text and len(text.strip()) > 100:
                        text_content = True
                        break

                if not text_content:
                    issues.append("No text content (likely scanned images)")
                    score -= 40

        except Exception as e:
            issues.append(f"Cannot read PDF: {e}")
            score = 0

        return {
            'score': score,
            'issues': issues,
            'is_valid': score >= 60
        }
```

### 2. Reference Extraction from PDFs
```python
class PDFReferenceExtractor:
    """Extract references from downloaded PDFs."""

    def extract_references(self, pdf_path: Path) -> list[str]:
        """Extract reference list from PDF."""

        try:
            import PyPDF2

            references = []

            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)

                # References usually at the end
                # Check last 30% of pages
                total_pages = len(reader.pages)
                start_page = int(total_pages * 0.7)

                for page_num in range(start_page, total_pages):
                    page = reader.pages[page_num]
                    text = page.extract_text()

                    # Look for "References" section
                    if 'references' in text.lower():
                        # Extract individual references
                        refs = self._parse_references(text)
                        references.extend(refs)

            return references

        except Exception as e:
            logger.error(f"Failed to extract references: {e}")
            return []

    def _parse_references(self, text: str) -> list[str]:
        """Parse individual references from text."""

        # Look for citation patterns
        # [1] Author. Title. Journal. Year;volume(issue):pages.
        import re

        patterns = [
            r'\[\d+\][^\[]+(?=\[\d+\]|$)',  # [1] ... [2] ...
            r'\d+\.\s+[A-Z][^.\n]+\.+[^.\n]+\.+\d{4}',  # Numbered
            r'[A-Z][a-z]+,\s+et\s+al\.[^.\n]+\.\d{4}',  # Author et al.
        ]

        references = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            references.extend(matches)

        return references[:50]  # Limit to 50
```

### 3. Citation Network Analysis
```python
class CitationNetwork:
    """Analyze citation connections between papers."""

    def __init__(self, config: Config):
        self.config = config
        self.semantic = SemanticScholarClient(config)

    def build_network(self, dois: list[str]) -> dict:
        """Build citation network for papers."""

        network = {
            'nodes': [],
            'edges': []
        }

        for doi in dois:
            # Get paper metadata
            paper = self.semantic.search_paper("", doi)
            if not paper:
                continue

            node = {
                'id': doi,
                'title': paper.get('title', ''),
                'year': paper.get('year', ''),
                'citationCount': paper.get('citationCount', 0),
                'influentialCitationCount': paper.get('influentialCitationCount', 0)
            }

            network['nodes'].append(node)

            # Get citations (papers that cite this one)
            citations = paper.get('citations', [])
            for citation in citations[:20]:  # Limit to 20
                if citation.get('doi') in dois:
                    network['edges'].append({
                        'source': citation['doi'],
                        'target': doi,
                        'type': 'cites'
                    })

        return network

    def find_related_papers(self, doi: str, limit: int = 10) -> list:
        """Find related papers based on citations."""

        # Get papers that cite this one
        # Get papers that this one cites
        # Look for co-citation patterns
        pass
```

---

## Priority 4: Workflow Improvements

### 1. Batch Processing
```python
class BatchProcessor:
    """Process multiple reference files at once."""

    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        resume: bool = True
    ) -> dict:
        """Process all reference files in directory."""

        results = {
            'files': [],
            'total_papers': 0,
            'total_downloaded': 0
        }

        # Find all reference files
        input_files = list(input_dir.glob("*.txt"))
        input_files.extend(input_dir.glob("*.bib"))
        input_files.extend(input_dir.glob("*.ris"))

        for i, input_file in enumerate(input_files, 1):
            logger.info(f"Processing {i}/{len(input_files)}: {input_file.name}")

            # Resolve DOIs
            output_csv = output_dir / f"{input_file.stem}_resolved.csv"
            resolver = DOIResolver(self.config)
            stats = resolver.resolve_references(
                input_file=input_file,
                output_csv=output_csv,
                resume=resume
            )

            # Download PDFs
            download_dir = output_dir / f"{input_file.stem}_pdfs"
            downloader = PDFDownloader(self.config)
            download_stats = downloader.run(
                input_csv=output_csv,
                output_dir=download_dir,
                resume=resume
            )

            results['files'].append({
                'input': str(input_file),
                'output_csv': str(output_csv),
                'papers': stats['total'],
                'downloaded': download_stats['downloaded']
            })

            results['total_papers'] += stats['total']
            results['total_downloaded'] += download_stats['downloaded']

        return results
```

### 2. Progress Database (for resumption)
```python
import sqlite3
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProgressRecord:
    """Track processing progress."""
    doi: str
    status: str  # pending, resolved, downloaded, failed
    timestamp: datetime
    source: str
    error: Optional[str] = None

class ProgressTracker:
    """Track progress across sessions using SQLite."""

    def __init__(self, db_path: Path = Path("progress.db")):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                doi TEXT PRIMARY KEY,
                status TEXT,
                timestamp TEXT,
                source TEXT,
                error TEXT,
                pdf_path TEXT
            )
        """)

        conn.commit()
        conn.close()

    def update(self, doi: str, status: str, source: str, error: str = None):
        """Update progress for a DOI."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO progress
            (doi, status, timestamp, source, error)
            VALUES (?, ?, ?, ?, ?)
        """, (doi, status, datetime.now().isoformat(), source, error))

        conn.commit()
        conn.close()

    def get_pending(self) -> list[str]:
        """Get list of pending DOIs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT doi FROM progress WHERE status = 'pending'
        """)

        dois = [row[0] for row in cursor.fetchall()]
        conn.close()

        return dois
```

### 3. Web Dashboard (FastAPI + Vue.js)
```python
# dashboard.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.get("/")
async def dashboard():
    """Serve web dashboard."""
    return HTMLResponse(open("templates/index.html").read())

@app.get("/api/stats")
async def get_stats():
    """Get processing statistics."""
    tracker = ProgressTracker()

    conn = sqlite3.connect(tracker.db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM progress
        GROUP BY status
    """)

    stats = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    return stats

@app.post("/api/process")
async def process_file(file: UploadFile):
    """Process uploaded reference file."""
    # Save file
    # Process with toolkit
    # Return results
    pass

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
```

---

## Priority 5: Advanced Features

### 1. Machine Learning Paper Matching
```python
class MLPaperMatcher:
    """Use ML to match papers across databases."""

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def find_best_match(
        self,
        title: str,
        candidates: list[dict]
    ) -> Optional[dict]:
        """Find best matching paper using embeddings."""

        # Encode title
        title_embedding = self.model.encode(title)

        # Encode candidates
        candidate_titles = [c['title'] for c in candidates]
        candidate_embeddings = self.model.encode(candidate_titles)

        # Calculate similarities
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(
            [title_embedding],
            candidate_embeddings
        )[0]

        # Find best match
        best_idx = similarities.argmax()
        best_similarity = similarities[best_idx]

        if best_similarity > 0.7:  # Threshold
            return candidates[best_idx]

        return None
```

### 2. Full-Text Search
```python
class FullTextSearch:
    """Search within downloaded PDFs."""

    def __init__(self, pdf_dir: Path):
        self.pdf_dir = pdf_dir
        self.index = self._build_index()

    def _build_index(self):
        """Build search index from PDFs."""
        import whoosh.index as index
        from whoosh.fields import Schema, TEXT, ID

        schema = Schema(
            path=ID(stored=True),
            title=TEXT(stored=True),
            content=TEXT(stored=True)
        )

        # Create index
        ix = index.create_in("indexdir", schema)
        writer = ix.writer()

        # Index all PDFs
        for pdf_path in self.pdf_dir.glob("*.pdf"):
            text = self._extract_text(pdf_path)
            title = pdf_path.stem

            writer.add_document(
                path=str(pdf_path),
                title=title,
                content=text
            )

        writer.commit()
        return ix

    def search(self, query: str, limit: int = 10) -> list:
        """Search PDFs for query."""
        from whoosh.qparser import QueryParser

        with self.index.searcher() as searcher:
            parser = QueryParser("content", self.index.schema)
            query_obj = parser.parse(query)

            results = searcher.search(query_obj, limit=limit)

            return [
                {
                    'path': r['path'],
                    'title': r['title'],
                    'score': r.score
                }
                for r in results
            ]
```

### 3. Automatic Deduplication
```python
class PaperDeduplicator:
    """Find and merge duplicate papers."""

    def find_duplicates(self, papers: list[dict]) -> list[list]:
        """Find groups of duplicate papers."""

        duplicates = []
        seen = {}

        for paper in papers:
            # Create fingerprint
            fingerprint = self._fingerprint(paper)

            if fingerprint in seen:
                duplicates.append([seen[fingerprint], paper])
            else:
                seen[fingerprint] = paper

        return duplicates

    def _fingerprint(self, paper: dict) -> str:
        """Create unique fingerprint for paper."""

        # Use title + year + first author
        title = paper.get('title', '').lower()
        year = paper.get('year', '')
        authors = paper.get('authors', '')
        first_author = authors.split(';')[0] if authors else ''

        # Normalize
        import re
        title = re.sub(r'[^\w\s]', '', title)
        first_author = re.sub(r'[^\w\s]', '', first_author)

        return f"{title}:{year}:{first_author}"
```

---

## Implementation Priority

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Rate limit handling | High | Medium | 1 |
| More preprint servers | Medium | Medium | 2 |
| Semantic Scholar | High | Low | 1 |
| Google Scholar search | High | Medium | 2 |
| PDF quality checker | Medium | Low | 2 |
| Reference extraction | Low | High | 3 |
| Batch processing | High | Medium | 2 |
| Progress database | Medium | Medium | 3 |
| Web dashboard | Medium | High | 4 |
| ML matching | Low | High | 4 |
| Full-text search | Low | Medium | 4 |

---

## Next Steps

Which features would you like me to implement first?

**Recommended starting points:**
1. **Semantic Scholar integration** (high impact, easy)
2. **Rate limit handling** (fixes current issues)
3. **PDF quality checking** (improves reliability)
4. **Batch processing** (workflow improvement)
