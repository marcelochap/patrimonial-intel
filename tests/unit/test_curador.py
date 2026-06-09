"""Unit tests for the Curador agent."""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_item(
    title: str,
    url: str,
    topic: str = "1",
    score: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "title": title,
        "date": "2026-06-09T08:00:00+00:00",
        "url": url,
        "source": "stf",
        "topic": topic,
        "snippet": "Snippet de teste.",
        "link_status": "verified",
        "summary": "Resumo de teste.",
        "legal_basis": None,
        "strategic_insight": "Insight de teste.",
        "comparison_table": None,
    }
    if score is not None:
        item["score"] = score
    item.update(kwargs)
    return item


class TestCurador:
    """Tests for agents.curador.Curador."""

    @pytest.mark.asyncio
    async def test_curador_removes_duplicate_urls(self):
        """Two items with the same URL should collapse to one."""
        pytest.skip("Curador not implemented yet")

        # from src.agents.curador import Curador
        # items = [
        #     _make_item("Título A", "https://stf.jus.br/1"),
        #     _make_item("Título B", "https://stf.jus.br/1"),  # duplicate URL
        # ]
        # curador = Curador(client=MagicMock())
        # result = await curador.deduplicate(items)
        # urls = [i["url"] for i in result]
        # assert len(urls) == len(set(urls))

    @pytest.mark.asyncio
    async def test_curador_removes_similar_titles(self):
        """Items whose titles share >80 % similarity should be deduplicated."""
        pytest.skip("Curador not implemented yet")

        # from src.agents.curador import Curador
        # items = [
        #     _make_item("STF decide sobre ITCMD em holdings", "https://stf.jus.br/1"),
        #     _make_item("STF decide sobre ITCMD em holdings familiares", "https://stf.jus.br/2"),
        # ]
        # curador = Curador(client=MagicMock())
        # result = await curador.deduplicate(items)
        # assert len(result) == 1

    @pytest.mark.asyncio
    async def test_curador_keeps_top_3_per_topic_by_score(self):
        """After scoring, at most 3 items per topic should survive."""
        pytest.skip("Curador not implemented yet")

        # from src.agents.curador import Curador
        # items = [
        #     _make_item(f"Notícia {i}", f"https://stf.jus.br/{i}", topic="1", score=float(i))
        #     for i in range(5)
        # ]
        # curador = Curador(client=MagicMock())
        # result = await curador.select_top(items, topic="1")
        # assert len(result) <= 3
        # scores = [r["score"] for r in result]
        # assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_curador_keeps_all_if_less_than_3(self):
        """A topic with only 2 items must not lose any of them."""
        pytest.skip("Curador not implemented yet")

        # from src.agents.curador import Curador
        # items = [
        #     _make_item("Notícia 1", "https://stf.jus.br/1", topic="2"),
        #     _make_item("Notícia 2", "https://stf.jus.br/2", topic="2"),
        # ]
        # curador = Curador(client=MagicMock())
        # result = await curador.select_top(items, topic="2")
        # assert len(result) == 2

    @pytest.mark.asyncio
    async def test_curador_score_calls_llm(self, mock_anthropic_client: MagicMock):
        """Scoring must invoke the Anthropic client at least once per item."""
        pytest.skip("Curador not implemented yet")

        # from src.agents.curador import Curador
        # items = [
        #     _make_item("Notícia A", "https://stf.jus.br/a"),
        #     _make_item("Notícia B", "https://stf.jus.br/b"),
        # ]
        # curador = Curador(client=mock_anthropic_client)
        # await curador.score_items(items)
        # assert mock_anthropic_client.messages.create.await_count >= len(items)
