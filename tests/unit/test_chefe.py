"""Unit tests for the Chefe agent (pipeline orchestrator)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Stubs used by multiple tests
# ---------------------------------------------------------------------------

def _make_agent_mock(name: str, return_value: Any = None) -> MagicMock:
    """Return an async-capable agent mock."""
    mock = MagicMock(name=name)
    mock.run = AsyncMock(return_value=return_value or [])
    return mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestChefe:
    """Tests for agents.chefe.Chefe."""

    @pytest.mark.asyncio
    async def test_pipeline_runs_all_agents_in_order(
        self, sample_validated_items: list[dict[str, Any]]
    ):
        """Chefe must call Investigador → Reporter → Curador → Validador → Design
        in that order when every step succeeds."""
        pytest.skip("Chefe not implemented yet")

        # call_order: list[str] = []
        #
        # def _track(name: str, retval: Any):
        #     async def _run(*args, **kwargs):
        #         call_order.append(name)
        #         return retval
        #     mock = MagicMock()
        #     mock.run = _run
        #     return mock
        #
        # from src.agents.chefe import Chefe
        # chefe = Chefe(
        #     investigador=_track("investigador", [sample_validated_items[0]]),
        #     reporter=_track("reporter", [sample_validated_items[0]]),
        #     curador=_track("curador", [sample_validated_items[0]]),
        #     validador=_track("validador", [sample_validated_items[0]]),
        #     design=_track("design", b"%PDF-"),
        # )
        # await chefe.run()
        # assert call_order == ["investigador", "reporter", "curador", "validador", "design"]

    @pytest.mark.asyncio
    async def test_chefe_retries_agent_on_failure(self):
        """If an agent fails once, Chefe must retry it and succeed on the second
        attempt without propagating the exception."""
        pytest.skip("Chefe not implemented yet")

        # from src.agents.chefe import Chefe
        # fail_once = AsyncMock(side_effect=[RuntimeError("flaky"), [{"topic": "1"}]])
        # reporter_mock = MagicMock()
        # reporter_mock.run = fail_once
        #
        # chefe = Chefe(reporter=reporter_mock, ...)
        # await chefe.run()  # should not raise
        # assert reporter_mock.run.await_count == 2

    @pytest.mark.asyncio
    async def test_chefe_sends_partial_report_when_2_topics_succeed(self):
        """When exactly 2 out of 5 topics produce validated items, Chefe must
        still generate a partial report rather than aborting entirely."""
        pytest.skip("Chefe not implemented yet")

        # from src.agents.chefe import Chefe
        # partial_items = [
        #     {"title": "T1", "topic": "1", "fact_status": "fact", "fact_confidence": 0.9},
        #     {"title": "T2", "topic": "2", "fact_status": "fact", "fact_confidence": 0.9},
        # ]
        # design_mock = MagicMock()
        # design_mock.run = AsyncMock(return_value=b"%PDF-")
        # chefe = Chefe(..., design=design_mock)
        # result = await chefe.run()
        # design_mock.run.assert_awaited_once()
        # assert result["status"] == "partial"

    @pytest.mark.asyncio
    async def test_chefe_fails_completely_when_0_topics_succeed(self):
        """When no topic produces any valid items, Chefe must raise a terminal
        error or return a failure status — not silently emit an empty report."""
        pytest.skip("Chefe not implemented yet")

        # from src.agents.chefe import Chefe, PipelineError
        # chefe = Chefe(investigador=_make_agent_mock("inv", return_value=[]), ...)
        # with pytest.raises(PipelineError):
        #     await chefe.run()

    @pytest.mark.asyncio
    async def test_chefe_logs_pipeline_steps_to_json(self, tmp_path: Path):
        """After a successful run, a JSON log file must exist and contain one
        entry per pipeline step."""
        pytest.skip("Chefe not implemented yet")

        # import importlib, sys
        # log_file = tmp_path / "pipeline.json"
        # from src.agents.chefe import Chefe
        # chefe = Chefe(..., log_path=log_file)
        # await chefe.run()
        # assert log_file.exists()
        # steps = json.loads(log_file.read_text())
        # step_names = [s["agent"] for s in steps]
        # assert "investigador" in step_names
        # assert "design" in step_names
