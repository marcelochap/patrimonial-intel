from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseScraper

SERPER_URL = "https://google.serper.dev/news"

# Sources without reliable RSS feeds — searched via Google News
NO_RSS_DOMAINS: list[str] = [
    "jota.info",
    "valor.com.br",
    "btgpactual.com",
    "xpi.com.br",
    "itau.com.br",
    "bradescobankprivate.com.br",
    "ans.gov.br",
    "susep.gov.br",
]


class GoogleSearchScraper(BaseScraper):
    source = "google_search"

    def __init__(
        self,
        api_key: str | None = None,
        domains: list[str] | None = None,
    ) -> None:
        self._api_key = api_key or os.environ["SERPER_API_KEY"]
        self._domains = domains or NO_RSS_DOMAINS

    async def fetch(self, topic: str, since_hours: int = 24) -> list[dict]:
        after_date = (
            datetime.now(tz=timezone.utc) - timedelta(hours=since_hours)
        ).strftime("%Y-%m-%d")

        results: list[dict] = []
        async with httpx.AsyncClient(timeout=30) as client:
            for domain in self._domains:
                items = await self._search_domain(client, domain, topic, after_date)
                results.extend(items)

        logger.info(f"[google_search] Collected {len(results)} items for topic={topic!r}")
        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _search_domain(
        self,
        client: httpx.AsyncClient,
        domain: str,
        topic: str,
        after_date: str,
    ) -> list[dict]:
        query = f"site:{domain} {topic} after:{after_date}"
        payload = {"q": query, "gl": "br", "hl": "pt-br", "num": 20}
        headers = {"X-API-KEY": self._api_key, "Content-Type": "application/json"}

        logger.debug(f"[google_search] Query: {query!r}")
        try:
            resp = await client.post(SERPER_URL, json=payload, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning(f"[google_search] HTTP {exc.response.status_code} for {domain}")
            return []
        except httpx.RequestError as exc:
            logger.error(f"[google_search] Request error for {domain}: {exc}")
            raise

        data = resp.json()
        news_items: list[dict] = data.get("news", [])

        results: list[dict] = []
        for item in news_items:
            date_raw = item.get("date", "")
            date_iso = self._normalize_date(date_raw) if date_raw else ""

            results.append({
                "title": item.get("title", "").strip(),
                "date": date_iso,
                "url": item.get("link", "").strip(),
                "source": domain,
                "snippet": (item.get("snippet") or "")[:300],
                "link_status": "unverified",
            })

        return results
