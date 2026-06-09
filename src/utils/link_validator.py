from __future__ import annotations

import asyncio

import httpx
from loguru import logger

_MAX_CONCURRENT = 10


async def validate_links(items: list[dict]) -> list[dict]:
    """Validate URLs for items where link_status != 'verified'.

    Runs HEAD requests in parallel (max 10 concurrent). Mutates items in-place
    and returns the same list for convenience.
    """
    to_validate = [i for i, item in enumerate(items) if item.get("link_status") != "verified"]

    if not to_validate:
        return items

    semaphore = asyncio.Semaphore(_MAX_CONCURRENT)

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(10.0),
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; patrimonial-intel/1.0)"},
    ) as client:
        tasks = [_check(client, semaphore, items, idx) for idx in to_validate]
        await asyncio.gather(*tasks)

    return items


async def _check(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    items: list[dict],
    idx: int,
) -> None:
    url: str = items[idx].get("url", "")
    if not url:
        items[idx]["link_status"] = "unavailable"
        return

    async with semaphore:
        try:
            resp = await client.head(url)
            final_url = str(resp.url)

            if 200 <= resp.status_code < 400:
                items[idx]["link_status"] = "verified"
                if final_url != url:
                    items[idx]["url"] = final_url
                    logger.debug(f"[link_validator] Redirect: {url} → {final_url}")
            elif resp.status_code in (404, 410):
                items[idx]["link_status"] = "unavailable"
                logger.info(f"[link_validator] Unavailable ({resp.status_code}): {url}")
            else:
                # 4xx/5xx other than gone — keep unverified to allow retry later
                logger.warning(f"[link_validator] Unexpected status {resp.status_code}: {url}")

        except httpx.TimeoutException:
            logger.warning(f"[link_validator] Timeout: {url}")
        except httpx.RequestError as exc:
            logger.warning(f"[link_validator] Request error for {url}: {exc}")
