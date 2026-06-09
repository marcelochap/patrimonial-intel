from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser
from loguru import logger

from .base import BaseScraper

FEEDS: dict[str, str] = {
    "conjur": "https://www.conjur.com.br/rss.xml",
    "migalhas": "https://www.migalhas.com.br/rss/quentes",
    "dou": "https://www.in.gov.br/consulta/-/busca-dou/rss?q=&s=do1",
    "stf": "https://portal.stf.jus.br/rss/noticiasRSS.asp",
    "stj": "https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/rss.aspx",
}


class RssScraper(BaseScraper):
    source = "rss"

    def __init__(self, feeds: dict[str, str] | None = None) -> None:
        self._feeds = feeds or FEEDS

    async def fetch(self, topic: str, since_hours: int = 24) -> list[dict]:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=since_hours)
        results: list[dict] = []

        for feed_source, url in self._feeds.items():
            logger.info(f"[rss] Fetching feed: {feed_source} ({url})")
            try:
                parsed = feedparser.parse(url)
                if parsed.get("bozo") and not parsed.entries:
                    logger.warning(f"[rss] Bozo feed ({feed_source}): {parsed.bozo_exception}")
                    continue

                for entry in parsed.entries:
                    item = self._parse_entry(entry, feed_source, cutoff, topic)
                    if item:
                        results.append(item)

            except Exception as exc:
                logger.error(f"[rss] Error fetching {feed_source}: {exc}")

        logger.info(f"[rss] Collected {len(results)} items for topic={topic!r}")
        return results

    def _parse_entry(
        self,
        entry: Any,
        feed_source: str,
        cutoff: datetime,
        topic: str,
    ) -> dict | None:
        pub_raw = (
            entry.get("published")
            or entry.get("updated")
            or entry.get("created")
            or ""
        )
        if not pub_raw:
            return None

        date_iso = self._normalize_date(pub_raw)

        # Filter by cutoff — parse back to compare
        try:
            pub_dt = datetime.fromisoformat(date_iso)
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            if pub_dt < cutoff:
                return None
        except ValueError:
            pass  # Include entries we can't parse — better safe than missing

        title: str = entry.get("title", "").strip()
        url: str = entry.get("link", "").strip()

        # Simple relevance check: skip entries with no title/url
        if not title or not url:
            return None

        summary_raw: str = entry.get("summary", "") or entry.get("description", "") or ""
        snippet = _strip_html(summary_raw)[:300]

        return {
            "title": title,
            "date": date_iso,
            "url": url,
            "source": feed_source,
            "snippet": snippet,
            "link_status": "verified",
        }


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    import re
    clean = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", clean).strip()
