from __future__ import annotations

import re
from datetime import datetime, timezone

from loguru import logger
from playwright.async_api import Browser, BrowserContext, async_playwright

from .base import BaseScraper


class PlaywrightScraper(BaseScraper):
    source = "playwright"

    def __init__(self) -> None:
        self._playwright = None
        self._browser: Browser | None = None

    async def _ensure_browser(self) -> Browser:
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            logger.debug("[playwright] Chromium browser launched")
        return self._browser

    async def fetch(self, topic: str, since_hours: int = 24) -> list[dict]:
        """Scrape a list of URLs. topic is treated as a URL when used as fallback."""
        # This scraper is invoked directly with a URL, not a search query.
        # When called from the pipeline, `topic` should be a fully-qualified URL.
        if not topic.startswith("http"):
            logger.warning(f"[playwright] Expected URL, got: {topic!r} — skipping")
            return []

        return await self._scrape_url(topic)

    async def scrape_urls(self, urls: list[str]) -> list[dict]:
        """Scrape multiple URLs and return all collected items."""
        results: list[dict] = []
        for url in urls:
            items = await self._scrape_url(url)
            results.extend(items)
        return results

    async def _scrape_url(self, url: str) -> list[dict]:
        browser = await self._ensure_browser()
        context: BrowserContext = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        try:
            page = await context.new_page()
            logger.info(f"[playwright] Navigating to {url}")
            await page.goto(url, timeout=15_000, wait_until="domcontentloaded")

            # Prefer <article> blocks; fall back to <main>, then <body>
            for selector in ("article", "main", "body"):
                elements = await page.query_selector_all(selector)
                if elements:
                    break

            items: list[dict] = []
            now_iso = datetime.now(tz=timezone.utc).isoformat()

            for el in elements[:10]:
                title_el = await el.query_selector("h1, h2, h3")
                title = (await title_el.inner_text()).strip() if title_el else ""

                link_el = await el.query_selector("a[href]")
                href = ""
                if link_el:
                    href = (await link_el.get_attribute("href") or "").strip()
                    if href.startswith("/"):
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        href = f"{parsed.scheme}://{parsed.netloc}{href}"

                text_content = (await el.inner_text()).strip()
                snippet = re.sub(r"\s+", " ", text_content)[:300]

                if not title:
                    continue

                items.append({
                    "title": title,
                    "date": now_iso,
                    "url": href or url,
                    "source": _domain_from_url(url),
                    "snippet": snippet,
                    "link_status": "verified",
                })

            logger.info(f"[playwright] Extracted {len(items)} items from {url}")
            return items

        except Exception as exc:
            logger.error(f"[playwright] Failed to scrape {url}: {exc}")
            return []
        finally:
            await context.close()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.debug("[playwright] Browser closed")


def _domain_from_url(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).netloc.removeprefix("www.")
