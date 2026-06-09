"""Unit tests for the Reporter agent."""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestReporter:
    """Tests for agents.reporter.Reporter."""

    # ------------------------------------------------------------------
    # Helper: build a minimal mock LLM response carrying JSON payload
    # ------------------------------------------------------------------

    @staticmethod
    def _llm_response(payload: dict) -> MagicMock:
        text_block = MagicMock()
        text_block.text = json.dumps(payload)

        resp = MagicMock()
        resp.content = [text_block]
        resp.usage = MagicMock(input_tokens=400, output_tokens=150)
        resp.model = "claude-sonnet-4-6"
        return resp

    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_reporter_generates_summary_for_valid_item(
        self, sample_raw_item: dict[str, Any], mock_anthropic_client: MagicMock
    ):
        """Reporter must return an item that contains summary, legal_basis,
        strategic_insight, and comparison_table keys after LLM call."""
        pytest.skip("Reporter not implemented yet")

        # Once implemented, replace skip with:
        # from src.agents.reporter import Reporter
        # reporter = Reporter(client=mock_anthropic_client)
        # result = await reporter.process_item(sample_raw_item)
        # assert "summary" in result
        # assert result["summary"]  # non-empty
        # assert "legal_basis" in result
        # assert "strategic_insight" in result
        # assert "comparison_table" in result

    @pytest.mark.asyncio
    async def test_reporter_handles_item_without_legal_basis(
        self, sample_raw_item: dict[str, Any]
    ):
        """When the LLM cannot identify a legal basis, legal_basis must be null,
        not a hallucinated value."""
        payload = {
            "summary": "Resumo da notícia.",
            "legal_basis": None,
            "strategic_insight": "Sem impacto imediato.",
            "comparison_table": None,
        }
        mock_response = self._llm_response(payload)

        client = MagicMock()
        client.messages.create = AsyncMock(return_value=mock_response)

        pytest.skip("Reporter not implemented yet")

        # from src.agents.reporter import Reporter
        # reporter = Reporter(client=client)
        # result = await reporter.process_item(sample_raw_item)
        # assert result["legal_basis"] is None

    @pytest.mark.asyncio
    async def test_reporter_generates_comparison_table_when_law_changes(
        self, sample_raw_item: dict[str, Any]
    ):
        """When the snippet describes a legislative change, comparison_table
        must have 'before' and 'after' keys with non-empty values."""
        payload = {
            "summary": "Nova lei altera regime tributário.",
            "legal_basis": "Lei 14.973/2024",
            "strategic_insight": "Revisar holdings antes de 2027.",
            "comparison_table": {
                "before": "Alíquota de 15% sobre ganhos de capital",
                "after": "Alíquota progressiva de 15%-22,5%",
            },
        }
        mock_response = self._llm_response(payload)

        client = MagicMock()
        client.messages.create = AsyncMock(return_value=mock_response)

        pytest.skip("Reporter not implemented yet")

        # from src.agents.reporter import Reporter
        # reporter = Reporter(client=client)
        # item = {**sample_raw_item, "snippet": "Nova lei altera alíquota de ganho de capital"}
        # result = await reporter.process_item(item)
        # assert result["comparison_table"] is not None
        # assert result["comparison_table"]["before"]
        # assert result["comparison_table"]["after"]

    @pytest.mark.asyncio
    async def test_reporter_uses_sonnet_model(
        self, sample_raw_item: dict[str, Any], mock_anthropic_client: MagicMock
    ):
        """The SDK call must use the claude-sonnet-4-6 model ID."""
        pytest.skip("Reporter not implemented yet")

        # from src.agents.reporter import Reporter, REPORTER_MODEL
        # assert REPORTER_MODEL == "claude-sonnet-4-6"
        #
        # reporter = Reporter(client=mock_anthropic_client)
        # await reporter.process_item(sample_raw_item)
        #
        # call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        # assert call_kwargs["model"] == "claude-sonnet-4-6"
