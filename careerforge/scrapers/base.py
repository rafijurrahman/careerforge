"""
CareerForge Scraper Plugin Architecture.
Defines BaseScraper ABC, JobPosting Pydantic model, politeness headers, rate limiting, and dedup helpers.
"""

import hashlib
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional

import requests
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from careerforge import __version__
except ImportError:
    __version__ = "0.1.0"


class JobPosting(BaseModel):
    """Unified schema for all job opportunities returned by CareerForge scrapers."""
    id: str
    title: str
    company: str
    location: str = "Remote"
    remote_policy: str = "Remote"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    posted_at: Optional[str] = None
    source_url: str
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


def compute_dedup_hash(company: str, title: str, location: str) -> str:
    """Calculates a deterministic SHA256 signature for deduplicating identical job postings."""
    norm_company = company.strip().lower()
    norm_title = re.sub(r'[^a-z0-9]', '', title.lower())
    norm_loc = re.sub(r'[^a-z0-9]', '', location.lower())
    signature = f"{norm_company}::{norm_title}::{norm_loc}"
    return hashlib.sha256(signature.encode("utf-8")).hexdigest()[:16]


def create_polite_session(rate_limit_per_sec: float = 2.0) -> requests.Session:
    """Creates a requests Session with CareerForge user-agent, timeouts, and exponential retries."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": f"CareerForge/{__version__} (https://github.com/careerforge/careerforge; open-source career engine)",
        "Accept": "application/json, text/plain, */*",
    })
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class BaseScraper(ABC):
    """Abstract Base Class that all CareerForge job board scanners must inherit from."""
    name: str = "base"
    requires_auth: bool = False
    rate_limit_per_sec: float = 2.0

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or create_polite_session(self.rate_limit_per_sec)
        self._last_request_time = 0.0

    def _throttle(self):
        """Enforces rate limiting between consecutive network requests."""
        if self.rate_limit_per_sec > 0:
            interval = 1.0 / self.rate_limit_per_sec
            elapsed = time.time() - self._last_request_time
            if elapsed < interval:
                time.sleep(interval - elapsed)
        self._last_request_time = time.time()

    @abstractmethod
    def fetch(self, config: Dict[str, Any]) -> Iterator[JobPosting]:
        """
        Executes job search against the target platform.
        Args:
            config: Dict containing keywords (List[str]), limit (int), exclude_senior (bool), etc.
        Yields:
            JobPosting instances.
        """
        pass

    def healthcheck(self) -> bool:
        """Verifies if the scraper target endpoint is responsive."""
        return True
