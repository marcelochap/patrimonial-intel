from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from loguru import logger

LinkStatus = Literal["verified", "unverified", "unavailable"]

_PT_MONTHS = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}

_BR_TZ = ZoneInfo("America/Sao_Paulo")


class BaseScraper(ABC):
    source: str = ""

    @abstractmethod
    async def fetch(self, topic: str, since_hours: int = 24) -> list[dict]:
        ...

    def _normalize_date(self, raw: str) -> str:
        """Convert pt-BR date strings and common HTTP date formats to ISO8601."""
        raw = raw.strip()

        # Already ISO-like: 2024-05-10T14:30:00...
        if re.match(r"\d{4}-\d{2}-\d{2}", raw):
            try:
                dt = datetime.fromisoformat(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=_BR_TZ)
                return dt.isoformat()
            except ValueError:
                pass

        # RFC 2822 from RSS: "Mon, 10 Jun 2024 14:30:00 +0000"
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(raw)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            pass

        # pt-BR: "10 de junho de 2024" / "10/06/2024" / "10 jun 2024"
        m = re.match(
            r"(\d{1,2})[/\s.-]de\s+(\w+)\s+de\s+(\d{4})", raw, re.IGNORECASE
        )
        if m:
            day, month_str, year = m.group(1), m.group(2).lower()[:3], m.group(3)
            month = _PT_MONTHS.get(month_str)
            if month:
                dt = datetime(int(year), month, int(day), tzinfo=_BR_TZ)
                return dt.isoformat()

        m = re.match(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", raw)
        if m:
            day, month, year = m.group(1), m.group(2), m.group(3)
            dt = datetime(int(year), int(month), int(day), tzinfo=_BR_TZ)
            return dt.isoformat()

        m = re.match(r"(\d{1,2})\s+(\w{3})\s+(\d{4})", raw, re.IGNORECASE)
        if m:
            day, month_str, year = m.group(1), m.group(2).lower(), m.group(3)
            month = _PT_MONTHS.get(month_str)
            if month:
                dt = datetime(int(year), month, int(day), tzinfo=_BR_TZ)
                return dt.isoformat()

        logger.warning(f"[{self.source}] Could not parse date: {raw!r}")
        return raw
