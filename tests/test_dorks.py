"""
Unit tests for the ATS Google Dork Generator.
"""

from careerforge.core.dorks import generate_ats_dorks


def test_generate_ats_dorks():
    dorks = generate_ats_dorks("Data Analyst", location="remote", extra_keywords="SQL")
    assert len(dorks) == 5

    platforms = [d["platform"] for d in dorks]
    assert "Greenhouse" in platforms
    assert "Lever" in platforms
    assert "Ashby" in platforms
    assert "Workable" in platforms
    assert "Hacker News" in platforms

    for d in dorks:
        assert "url" in d
        assert d["url"].startswith("https://www.google.com/search?q=")
        assert "Data Analyst" in d["dork"]
