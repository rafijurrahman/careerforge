"""
Offline contract tests for CareerForge scrapers using recorded fixtures.
Ensures scrapers produce valid JobPosting objects without opening network sockets.
"""

import json
import os
from unittest.mock import MagicMock

from careerforge.scrapers.ashby_scanner import AshbyScraper
from careerforge.scrapers.base import JobPosting, compute_dedup_hash
from careerforge.scrapers.greenhouse_scanner import GreenhouseScraper
from careerforge.scrapers.remotive_scanner import RemotiveScraper


def load_fixture(filename: str):
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_greenhouse_scraper_offline_fixture():
    fixture_data = load_fixture("greenhouse_sample.json")
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fixture_data
    mock_session.get.return_value = mock_resp

    scraper = GreenhouseScraper(session=mock_session, boards=["canonical"])
    postings = list(scraper.fetch({"keywords": ["Backend", "Engineer"], "exclude_senior": True}))

    assert len(postings) == 1
    p = postings[0]
    assert isinstance(p, JobPosting)
    assert p.company == "Canonical"
    assert "Backend" in p.title
    assert p.source == "Greenhouse"
    assert "https://" in p.source_url


def test_ashby_scraper_offline_fixture():
    fixture_data = load_fixture("ashby_sample.json")
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fixture_data
    mock_session.get.return_value = mock_resp

    scraper = AshbyScraper(session=mock_session, boards=["linear"])
    postings = list(scraper.fetch({"keywords": ["Data Analyst"], "exclude_senior": True}))

    assert len(postings) == 1
    p = postings[0]
    assert isinstance(p, JobPosting)
    assert p.company == "Linear"
    assert "Data Analyst" in p.title
    assert p.source == "Ashby"


def test_remotive_scraper_offline_fixture():
    fixture_data = load_fixture("remotive_sample.json")
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fixture_data
    mock_session.get.return_value = mock_resp

    scraper = RemotiveScraper(session=mock_session)
    postings = list(scraper.fetch({"target_roles": ["Business Intelligence Analyst"]}))

    assert len(postings) == 1
    p = postings[0]
    assert isinstance(p, JobPosting)
    assert p.company == "CloudMetrics"
    assert p.source == "Remotive"


def test_compute_dedup_hash():
    h1 = compute_dedup_hash("Acme Corp", "Data Analyst", "Remote")
    h2 = compute_dedup_hash(" acme corp ", "DATA ANALYST", "remote ")
    h3 = compute_dedup_hash("Other Corp", "Data Analyst", "Remote")

    assert h1 == h2, "Dedup hash must normalize whitespace and casing"
    assert h1 != h3, "Different companies must have different signatures"
