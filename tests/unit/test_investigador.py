"""Unit tests for the Investigador agent and its scrapers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_feed_entry(
    title: str,
    url: str,
    published: str,
    summary: str = "snippet",
) -> MagicMock:
    """Build a feedparser-like entry MagicMock."""
    entry = MagicMock()
    entry.get = lambda key, default="": {
        "title": title,
        "link": url,
        "published": published,
        "summary": summary,
    }.get(key, default)
    entry.title = title
    entry.link = url
    entry.published = published
    entry.summary = summary
    return entry


def _rfc2822(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


# ---------------------------------------------------------------------------
# RSS Scraper
# ---------------------------------------------------------------------------

class TestRssScraper:
    """Tests for scrapers.rss_scraper.RssScraper."""

    @pytest.mark.asyncio
    async def test_rss_scraper_returns_items_within_24h(self):
        """Entries published within 24 h should be returned."""
        from src.scrapers.rss_scraper import RssScraper

        now = datetime.now(tz=timezone.utc)
        recent_pub = _rfc2822(now - timedelta(hours=6))
        entry = _make_feed_entry(
            title="STF decide sobre ITCMD",
            url="https://stf.jus.br/noticia/1",
            published=recent_pub,
        )

        fake_feed = MagicMock()
        fake_feed.entries = [entry]
        fake_feed.get = lambda key, default=None: default  # bozo=None

        with patch("src.scrapers.rss_scraper._fetch_feed_raw", return_value=b"<rss/>"), \
             patch("feedparser.parse", return_value=fake_feed):
            scraper = RssScraper(feeds={"stf": "https://stf.jus.br/rss"})
            results = await scraper.fetch(topic="1")

        assert len(results) == 1
        assert results[0]["title"] == "STF decide sobre ITCMD"
        assert results[0]["source"] == "stf"

    @pytest.mark.asyncio
    async def test_rss_scraper_ignores_old_entries(self):
        """Entries older than 24 h must be filtered out."""
        from src.scrapers.rss_scraper import RssScraper

        now = datetime.now(tz=timezone.utc)
        old_pub = _rfc2822(now - timedelta(hours=48))
        entry = _make_feed_entry(
            title="Notícia antiga",
            url="https://stf.jus.br/noticia/old",
            published=old_pub,
        )

        fake_feed = MagicMock()
        fake_feed.entries = [entry]
        fake_feed.get = lambda key, default=None: default

        with patch("src.scrapers.rss_scraper._fetch_feed_raw", return_value=b"<rss/>"), \
             patch("feedparser.parse", return_value=fake_feed):
            scraper = RssScraper(feeds={"stf": "https://stf.jus.br/rss"})
            results = await scraper.fetch(topic="1")

        assert results == []


# ---------------------------------------------------------------------------
# Google Search Scraper
# ---------------------------------------------------------------------------

class TestGoogleSearchScraper:
    """Tests for scrapers.google_search.GoogleSearchScraper."""

    @pytest.mark.asyncio
    async def test_google_search_scraper_builds_correct_query(self):
        """Scraper must build a query that includes the topic keyword."""
        pytest.skip("GoogleSearchScraper not implemented yet")

    @pytest.mark.asyncio
    async def test_google_search_scraper_handles_api_error(self):
        """A 429 response must trigger a retry, not a crash."""
        pytest.skip("GoogleSearchScraper not implemented yet — retry logic pending")


# ---------------------------------------------------------------------------
# Link Validator
# ---------------------------------------------------------------------------

class TestLinkValidator:
    """Tests for utils.link_validator (or equivalent module)."""

    @pytest.mark.asyncio
    async def test_link_validator_marks_verified(
        self, sample_raw_item: dict[str, Any], mock_httpx_client: MagicMock
    ):
        """HEAD 200 → link_status == 'verified'."""
        pytest.skip("LinkValidator not implemented yet")

    @pytest.mark.asyncio
    async def test_link_validator_marks_unavailable(
        self, sample_raw_item: dict[str, Any]
    ):
        """HEAD 404 → link_status == 'unavailable'."""
        pytest.skip("LinkValidator not implemented yet")

    @pytest.mark.asyncio
    async def test_link_validator_marks_unverified_on_timeout(
        self, sample_raw_item: dict[str, Any]
    ):
        """Timeout → link_status == 'unverified' (no crash)."""
        pytest.skip("LinkValidator not implemented yet")


# ---------------------------------------------------------------------------
# Investigador agent
# ---------------------------------------------------------------------------

class TestInvestigador:
    """Tests for agents.investigador.Investigador."""

    @pytest.mark.asyncio
    async def test_investigador_deduplicates_same_url_across_scrapers(self):
        """If two scrapers return the same URL, only one item must appear in output."""
        pytest.skip("Investigador not implemented yet")
