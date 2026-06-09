from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from loguru import logger
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from src.scrapers import GoogleSearchScraper, PlaywrightScraper, RssScraper
from src.scrapers.rss_scraper import FEEDS
from src.utils.cost_tracker import CostTracker
from src.utils.link_validator import validate_links

BASE_DIR = Path(__file__).parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
RAW_DIR = OUTPUTS_DIR / "raw"
SEEN_URLS_PATH = OUTPUTS_DIR / "seen_urls.json"

TOPICS: dict[str, dict[str, Any]] = {
    "1_sucessorio": {
        "label": "Patrimonial e Sucessório",
        "keywords": ["ITCMD", "inventário", "trust", "planejamento sucessório", "herança", "doação"],
        "sources_rss": ["conjur", "migalhas"],
        "sources_search": ["jota.info", "valor.com.br"],
    },
    "2_tributario": {
        "label": "Tributário",
        "keywords": ["IRPF", "dividendos", "ganho de capital", "CARF", "imposto de renda"],
        "sources_rss": ["conjur", "migalhas", "stf", "stj"],
        "sources_search": ["jota.info", "valor.com.br"],
    },
    "3_imobiliario": {
        "label": "Imobiliário e Família",
        "keywords": ["contrato imobiliário", "regime de bens", "incorporação", "compra e venda imóvel"],
        "sources_rss": ["conjur", "migalhas"],
        "sources_search": ["jota.info"],
    },
    "4_holdings": {
        "label": "Holdings",
        "keywords": ["holding familiar", "acordo de sócios", "governança corporativa", "proteção patrimonial"],
        "sources_rss": ["conjur", "migalhas"],
        "sources_search": ["jota.info", "btgpactual.com", "conteudos.xpi.com.br"],
    },
    "5_seguros": {
        "label": "Seguros",
        "keywords": ["seguro de vida", "seguro invalidez", "ANS", "SUSEP", "seguro saúde", "previdência privada"],
        "sources_rss": ["ans", "susep", "conjur"],
        "sources_search": ["jota.info", "ans.gov.br", "susep.gov.br"],
    },
}


def _load_seen_urls() -> dict[str, str]:
    if not SEEN_URLS_PATH.exists():
        return {}
    try:
        data: dict[str, str] = json.loads(SEEN_URLS_PATH.read_text(encoding="utf-8"))
        cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=7)).isoformat()
        return {url: date for url, date in data.items() if date >= cutoff}
    except Exception as exc:
        logger.warning(f"[investigador] Failed to load seen_urls.json: {exc}")
        return {}


def _save_seen_urls(seen: dict[str, str]) -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_URLS_PATH.write_text(
        json.dumps(seen, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _deduplicate(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(item)
    return unique


def _is_keyword_relevant(item: dict, keywords: list[str]) -> bool:
    text = (item.get("title", "") + " " + item.get("snippet", "")).lower()
    return any(kw.lower() in text for kw in keywords)


async def _fetch_topic(
    topic_key: str,
    topic_cfg: dict[str, Any],
    cost_tracker: CostTracker,
) -> tuple[str, list[dict], list[dict]]:
    """Collect news for a single topic using RSS → Google Search → Playwright fallback."""
    items: list[dict] = []
    errors: list[dict] = []
    keywords: list[str] = topic_cfg["keywords"]
    query_str = " OR ".join(keywords[:3])

    # --- RSS ---
    rss_feeds = {k: v for k, v in FEEDS.items() if k in topic_cfg["sources_rss"]}
    if rss_feeds:
        logger.info(f"[investigador] [{topic_key}] Trying RSS ({list(rss_feeds.keys())})")
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                reraise=True,
            ):
                with attempt:
                    rss = RssScraper(feeds=rss_feeds)
                    rss_items = await rss.fetch(topic=query_str)

            relevant = [i for i in rss_items if _is_keyword_relevant(i, keywords)]
            for item in relevant:
                item["topic"] = topic_key
            items.extend(relevant)
            logger.info(f"[investigador] [{topic_key}] RSS: {len(relevant)} relevant items")
        except Exception as exc:
            logger.warning(f"[investigador] [{topic_key}] RSS failed: {exc}")
            errors.append({"topic": topic_key, "scraper": "rss", "error": str(exc)})

    # --- Google Search ---
    search_domains = topic_cfg.get("sources_search", [])
    if search_domains:
        logger.info(f"[investigador] [{topic_key}] Trying Google Search ({search_domains})")
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                reraise=True,
            ):
                with attempt:
                    gs = GoogleSearchScraper(domains=search_domains)
                    gs_items = await gs.fetch(topic=query_str)

            relevant_gs = [i for i in gs_items if _is_keyword_relevant(i, keywords)]
            for item in relevant_gs:
                item["topic"] = topic_key
            items.extend(relevant_gs)
            logger.info(f"[investigador] [{topic_key}] Google Search: {len(relevant_gs)} relevant items")
        except Exception as exc:
            logger.warning(f"[investigador] [{topic_key}] Google Search failed: {exc}")
            errors.append({"topic": topic_key, "scraper": "google_search", "error": str(exc)})

    # --- Playwright fallback (only when both previous scrapers yielded nothing) ---
    if not items:
        logger.warning(
            f"[investigador] [{topic_key}] No items from RSS/Search — falling back to Playwright"
        )
        fallback_urls = [f"https://www.{d}" for d in search_domains[:2]]
        for url in fallback_urls:
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=1, min=2, max=10),
                    reraise=True,
                ):
                    with attempt:
                        pw = PlaywrightScraper()
                        pw_items = await pw.fetch(topic=query_str)

                for item in pw_items:
                    item["topic"] = topic_key
                items.extend(pw_items)
                logger.info(
                    f"[investigador] [{topic_key}] Playwright ({url}): {len(pw_items)} items"
                )
                break
            except Exception as exc:
                logger.error(f"[investigador] [{topic_key}] Playwright failed for {url}: {exc}")
                errors.append({"topic": topic_key, "scraper": "playwright", "error": str(exc)})

    items = _deduplicate(items)
    return topic_key, items, errors


async def main() -> None:
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    logger.info(f"[investigador] Starting collection for {date_str}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cost_tracker = CostTracker()
    seen_urls = _load_seen_urls()
    logger.info(f"[investigador] Loaded {len(seen_urls)} seen URLs from cache")

    tasks = [
        _fetch_topic(topic_key, topic_cfg, cost_tracker)
        for topic_key, topic_cfg in TOPICS.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    topics_out: dict[str, list[dict]] = {}
    all_errors: list[dict] = []
    total_items = 0

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"[investigador] Topic task raised exception: {result}")
            all_errors.append({"topic": "unknown", "scraper": "gather", "error": str(result)})
            continue

        topic_key, items, errors = result
        all_errors.extend(errors)

        # Filter already-seen URLs
        new_items = [i for i in items if i.get("url", "") not in seen_urls]
        skipped = len(items) - len(new_items)
        if skipped:
            logger.info(f"[investigador] [{topic_key}] Skipped {skipped} already-seen URLs")

        # Validate links
        if new_items:
            new_items = await validate_links(new_items)

        topics_out[topic_key] = new_items
        total_items += len(new_items)
        logger.info(f"[investigador] [{topic_key}] Final: {len(new_items)} new items")

    # Update seen_urls cache with all collected URLs
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    for items in topics_out.values():
        for item in items:
            url = item.get("url", "")
            if url:
                seen_urls[url] = now_iso
    _save_seen_urls(seen_urls)
    logger.info(f"[investigador] Saved seen_urls cache ({len(seen_urls)} total entries)")

    output: dict[str, Any] = {
        "date": date_str,
        "topics": topics_out,
        "total_items": total_items,
        "errors": all_errors,
    }

    out_path = RAW_DIR / f"investigador_{date_str}.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"[investigador] Output saved to {out_path} ({total_items} total items)")

    cost_path = cost_tracker.save()
    logger.info(f"[investigador] Cost report saved to {cost_path}")


if __name__ == "__main__":
    asyncio.run(main())
