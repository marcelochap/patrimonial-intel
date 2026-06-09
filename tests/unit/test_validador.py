"""Unit tests for the Validador agent."""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


def _item_with_snippet(snippet: str, **kwargs: Any) -> dict[str, Any]:
    return {
        "title": "Título de teste",
        "date": "2026-06-09T08:00:00+00:00",
        "url": "https://stf.jus.br/noticia/1",
        "source": "stf",
        "topic": "1",
        "snippet": snippet,
        "link_status": "verified",
        "summary": snippet,
        "legal_basis": None,
        "strategic_insight": "Insight.",
        "comparison_table": None,
        **kwargs,
    }


class TestHeuristic:
    """Tests for the speculation-detection heuristic inside Validador."""

    def test_heuristic_detects_speculation_keywords(self):
        """Items containing 'poderia', 'teria', or 'especula-se' must be
        classified as speculation by the heuristic alone."""
        pytest.skip("Validador not implemented yet")

        # from src.agents.validador import classify_heuristic
        # speculation_snippets = [
        #     "A medida poderia afetar holdings familiares em todo o país.",
        #     "O ministro teria votado contrariamente ao relator.",
        #     "Especula-se que o julgamento será retomado em agosto.",
        # ]
        # for snippet in speculation_snippets:
        #     item = _item_with_snippet(snippet)
        #     label, confidence = classify_heuristic(item)
        #     assert label == "speculation", f"Expected speculation for: {snippet!r}"
        #     assert confidence < 0.7

    def test_heuristic_marks_fact_for_stf_decision(self):
        """A snippet describing a concluded STF decision must score as 'fact'
        with confidence >= 0.7."""
        pytest.skip("Validador not implemented yet")

        # from src.agents.validador import classify_heuristic
        # snippet = (
        #     "O STF, por unanimidade, negou provimento ao RE 1.425.609, "
        #     "fixando a tese de repercussão geral no Tema 1.369."
        # )
        # item = _item_with_snippet(snippet)
        # label, confidence = classify_heuristic(item)
        # assert label == "fact"
        # assert confidence >= 0.7


class TestLlmEscalation:
    """Tests for the LLM escalation path in Validador."""

    @pytest.mark.asyncio
    async def test_ambiguous_item_escalates_to_llm(self, mock_anthropic_client: MagicMock):
        """Items whose heuristic confidence < 0.7 must trigger an LLM call
        using the haiku model."""
        pytest.skip("Validador not implemented yet")

        # from src.agents.validador import Validador
        # item = _item_with_snippet("Talvez o governo decida algo sobre holdings.")
        # # Simulate heuristic returning low-confidence result
        # validador = Validador(client=mock_anthropic_client)
        # await validador.classify_item(item)
        # call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        # assert "haiku" in call_kwargs["model"]

    @pytest.mark.asyncio
    async def test_llm_classification_stored_correctly(self, mock_anthropic_client: MagicMock):
        """After LLM classification the item must carry fact_status and
        fact_confidence at the top level."""
        llm_payload = {"fact_status": "opinion", "fact_confidence": 0.82}
        text_block = MagicMock()
        text_block.text = json.dumps(llm_payload)
        resp = MagicMock()
        resp.content = [text_block]
        resp.usage = MagicMock(input_tokens=100, output_tokens=30)
        mock_anthropic_client.messages.create = AsyncMock(return_value=resp)

        pytest.skip("Validador not implemented yet")

        # from src.agents.validador import Validador
        # item = _item_with_snippet("Decisão poderia mudar tributação.")
        # validador = Validador(client=mock_anthropic_client)
        # result = await validador.classify_item(item)
        # assert result["fact_status"] == "opinion"
        # assert abs(result["fact_confidence"] - 0.82) < 1e-6


class TestValidadorPipeline:
    """Tests for the overall Validador.run() flow."""

    @pytest.mark.asyncio
    async def test_link_validation_runs_before_fact_check(
        self, sample_curated_items: list[dict[str, Any]], mock_httpx_client: MagicMock
    ):
        """link_status must be set on each item before fact classification runs."""
        pytest.skip("Validador not implemented yet")

        # The key contract: when we inspect calls, httpx HEAD must precede
        # any LLM messages.create call.
        #
        # from src.agents.validador import Validador
        # call_order: list[str] = []
        # mock_httpx_client.head.side_effect = lambda *a, **kw: call_order.append("http") or ...
        # mock_anthropic_client.messages.create.side_effect = lambda **kw: call_order.append("llm") or ...
        # validador = Validador(client=mock_anthropic_client, http_client=mock_httpx_client)
        # await validador.run(sample_curated_items)
        # first_llm = next(i for i, v in enumerate(call_order) if v == "llm")
        # last_http = max(i for i, v in enumerate(call_order) if v == "http")
        # assert last_http < first_llm
