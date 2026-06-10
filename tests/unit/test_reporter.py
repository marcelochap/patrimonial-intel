"""Unit tests for src/agents/reporter.py"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_llm_response(payload: dict) -> MagicMock:
    """Build a mock Anthropic message response carrying a JSON payload."""
    text_block = MagicMock()
    text_block.text = json.dumps(payload, ensure_ascii=False)

    resp = MagicMock()
    resp.content = [text_block]
    resp.usage = MagicMock(input_tokens=400, output_tokens=150)
    return resp


_VALID_PAYLOAD = {
    "summary": "O STF decidiu sobre ITCMD em holdings familiares.",
    "legal_basis": "Art. 155, I, CF/88; RE 1.425.609",
    "strategic_insight": "Revisar cláusulas de integralização.",
    "comparison_table": None,
}

_CHANGE_PAYLOAD = {
    "summary": "Nova alíquota progressiva de ganho de capital.",
    "legal_basis": "Lei 14.973/2024",
    "strategic_insight": "Revisar holdings antes de 2027.",
    "comparison_table": {
        "before": "Alíquota flat de 15%",
        "after": "Alíquota progressiva 15%–22,5%",
    },
}


# ---------------------------------------------------------------------------
# Tests for _process_item (core LLM call unit)
# ---------------------------------------------------------------------------

class TestProcessItem:

    @pytest.mark.asyncio
    async def test_returns_all_required_fields(self, sample_raw_item: dict[str, Any]):
        """Processed item must contain summary, legal_basis, strategic_insight, comparison_table."""
        from src.agents.reporter import _process_item
        from src.utils.cost_tracker import CostTracker

        client = MagicMock()
        client.messages.create = AsyncMock(return_value=_mock_llm_response(_VALID_PAYLOAD))

        result = await _process_item(client, CostTracker(), sample_raw_item)

        assert result["summary"] == _VALID_PAYLOAD["summary"]
        assert result["legal_basis"] == _VALID_PAYLOAD["legal_basis"]
        assert result["strategic_insight"] == _VALID_PAYLOAD["strategic_insight"]
        assert result["comparison_table"] is None
        # Original fields preserved
        assert result["title"] == sample_raw_item["title"]
        assert result["url"] == sample_raw_item["url"]

    @pytest.mark.asyncio
    async def test_legal_basis_none_when_not_in_text(self, sample_raw_item: dict[str, Any]):
        """legal_basis must be null when LLM returns null — never hallucinated."""
        from src.agents.reporter import _process_item
        from src.utils.cost_tracker import CostTracker

        payload = {**_VALID_PAYLOAD, "legal_basis": None}
        client = MagicMock()
        client.messages.create = AsyncMock(return_value=_mock_llm_response(payload))

        result = await _process_item(client, CostTracker(), sample_raw_item)
        assert result["legal_basis"] is None

    @pytest.mark.asyncio
    async def test_comparison_table_populated_when_law_changes(self, sample_raw_item: dict[str, Any]):
        """comparison_table must have before/after when LLM detects a legislative change."""
        from src.agents.reporter import _process_item
        from src.utils.cost_tracker import CostTracker

        client = MagicMock()
        client.messages.create = AsyncMock(return_value=_mock_llm_response(_CHANGE_PAYLOAD))

        result = await _process_item(client, CostTracker(), sample_raw_item)

        assert result["comparison_table"] is not None
        assert result["comparison_table"]["before"]
        assert result["comparison_table"]["after"]

    @pytest.mark.asyncio
    async def test_uses_sonnet_model(self, sample_raw_item: dict[str, Any]):
        """The SDK call must use claude-sonnet-4-6 model ID."""
        from src.agents import reporter
        from src.utils.cost_tracker import CostTracker

        assert reporter._MODEL == "claude-sonnet-4-6"

        client = MagicMock()
        create_mock = AsyncMock(return_value=_mock_llm_response(_VALID_PAYLOAD))
        client.messages.create = create_mock

        await reporter._process_item(client, CostTracker(), sample_raw_item)

        call_kwargs = create_mock.call_args.kwargs
        assert call_kwargs["model"] == "claude-sonnet-4-6"

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_json(self, sample_raw_item: dict[str, Any]):
        """When LLM returns invalid JSON twice, item gets fallback values (not an exception)."""
        from src.agents.reporter import _process_item
        from src.utils.cost_tracker import CostTracker

        bad_resp = MagicMock()
        bad_resp.content = [MagicMock(text="este não é json válido {{{")]
        bad_resp.usage = MagicMock(input_tokens=100, output_tokens=10)

        client = MagicMock()
        client.messages.create = AsyncMock(return_value=bad_resp)

        result = await _process_item(client, CostTracker(), sample_raw_item)

        # Should not raise — should use fallback
        assert "summary" in result
        assert result["strategic_insight"] == "Não foi possível processar."

    @pytest.mark.asyncio
    async def test_records_cost_after_successful_call(self, sample_raw_item: dict[str, Any]):
        """CostTracker must have an entry for 'reporter' after processing one item."""
        from src.agents.reporter import _process_item
        from src.utils.cost_tracker import CostTracker

        client = MagicMock()
        client.messages.create = AsyncMock(return_value=_mock_llm_response(_VALID_PAYLOAD))

        tracker = CostTracker()
        await _process_item(client, tracker, sample_raw_item)

        summary = tracker.summary()
        assert "reporter" in summary["agents"]
        assert summary["total_cost_usd"] > 0


# ---------------------------------------------------------------------------
# Tests for run() — integration-level with mocked LLM
# ---------------------------------------------------------------------------

class TestRunFunction:

    @pytest.mark.asyncio
    async def test_run_reads_wrapped_topics_format(self, tmp_path: Path, sample_raw_item: dict[str, Any]):
        """run() must handle the {date, topics: {topic: [items]}} envelope from Investigador."""
        from src.agents.reporter import run
        from src.utils.cost_tracker import CostTracker

        input_data = {
            "date": "2026-06-10",
            "topics": {
                "2_tributario": [sample_raw_item],
            },
            "total_items": 1,
            "errors": [],
        }
        input_file = tmp_path / "investigador_2026-06-10.json"
        input_file.write_text(json.dumps(input_data, ensure_ascii=False), encoding="utf-8")
        output_file = tmp_path / "reporter_2026-06-10.json"

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create = AsyncMock(return_value=_mock_llm_response(_VALID_PAYLOAD))
            mock_cls.return_value = mock_client

            result_path = await run(input_file, output_file)

        output = json.loads(result_path.read_text(encoding="utf-8"))
        assert "2_tributario" in output
        items = output["2_tributario"]
        assert len(items) == 1
        assert items[0]["summary"] == _VALID_PAYLOAD["summary"]

    @pytest.mark.asyncio
    async def test_run_handles_flat_format(self, tmp_path: Path, sample_raw_item: dict[str, Any]):
        """run() must also handle flat {topic: [items]} format (no envelope)."""
        from src.agents.reporter import run

        input_data = {"2_tributario": [sample_raw_item]}
        input_file = tmp_path / "flat.json"
        input_file.write_text(json.dumps(input_data, ensure_ascii=False), encoding="utf-8")
        output_file = tmp_path / "out.json"

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create = AsyncMock(return_value=_mock_llm_response(_VALID_PAYLOAD))
            mock_cls.return_value = mock_client

            result_path = await run(input_file, output_file)

        output = json.loads(result_path.read_text(encoding="utf-8"))
        assert "2_tributario" in output

    @pytest.mark.asyncio
    async def test_run_writes_output_file(self, tmp_path: Path, sample_raw_item: dict[str, Any]):
        """run() must write a JSON file at the specified output path."""
        from src.agents.reporter import run

        input_data = {"date": "2026-06-10", "topics": {"1_sucessorio": [sample_raw_item]}, "total_items": 1, "errors": []}
        input_file = tmp_path / "inv.json"
        input_file.write_text(json.dumps(input_data), encoding="utf-8")
        output_file = tmp_path / "rep.json"

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create = AsyncMock(return_value=_mock_llm_response(_VALID_PAYLOAD))
            mock_cls.return_value = mock_client
            await run(input_file, output_file)

        assert output_file.exists()
        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
