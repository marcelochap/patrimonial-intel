"""Unit tests for the CostTracker utility."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

# Pricing constants (per 1 M tokens, USD)
HAIKU_INPUT_PER_1M = 0.80
HAIKU_OUTPUT_PER_1M = 4.00
SONNET_INPUT_PER_1M = 3.00
SONNET_OUTPUT_PER_1M = 15.00


class TestCostTracker:
    """Tests for utils.cost_tracker.CostTracker (or equivalent module)."""

    def test_records_cost_per_agent(self):
        """After recording usage for two agents, both must appear in the
        tracker summary with non-zero cost values."""
        pytest.skip("CostTracker not implemented yet")

        # from src.utils.cost_tracker import CostTracker
        # tracker = CostTracker()
        # tracker.record(
        #     agent="reporter",
        #     model="claude-sonnet-4-6",
        #     input_tokens=1_000,
        #     output_tokens=500,
        # )
        # tracker.record(
        #     agent="validador",
        #     model="claude-haiku-4-5",
        #     input_tokens=2_000,
        #     output_tokens=300,
        # )
        # summary = tracker.summary()
        # assert "reporter" in summary
        # assert "validador" in summary
        # assert summary["reporter"]["usd"] > 0
        # assert summary["validador"]["usd"] > 0

    def test_summary_calculates_usd_correctly(self):
        """USD total must match the expected formula for known token counts."""
        pytest.skip("CostTracker not implemented yet")

        # from src.utils.cost_tracker import CostTracker
        #
        # tracker = CostTracker()
        # # Haiku: 500k input + 100k output
        # tracker.record(
        #     agent="validador",
        #     model="claude-haiku-4-5",
        #     input_tokens=500_000,
        #     output_tokens=100_000,
        # )
        # # Sonnet: 200k input + 50k output
        # tracker.record(
        #     agent="reporter",
        #     model="claude-sonnet-4-6",
        #     input_tokens=200_000,
        #     output_tokens=50_000,
        # )
        # summary = tracker.summary()
        #
        # expected_haiku = (
        #     (500_000 / 1_000_000) * HAIKU_INPUT_PER_1M
        #     + (100_000 / 1_000_000) * HAIKU_OUTPUT_PER_1M
        # )
        # expected_sonnet = (
        #     (200_000 / 1_000_000) * SONNET_INPUT_PER_1M
        #     + (50_000 / 1_000_000) * SONNET_OUTPUT_PER_1M
        # )
        # assert abs(summary["validador"]["usd"] - expected_haiku) < 1e-6
        # assert abs(summary["reporter"]["usd"] - expected_sonnet) < 1e-6
        # assert abs(summary["total_usd"] - (expected_haiku + expected_sonnet)) < 1e-6

    def test_saves_json_file(self, tmp_path: Path):
        """CostTracker.save() must write a valid JSON file at the given path."""
        pytest.skip("CostTracker not implemented yet")

        # from src.utils.cost_tracker import CostTracker
        # tracker = CostTracker()
        # tracker.record(
        #     agent="reporter",
        #     model="claude-sonnet-4-6",
        #     input_tokens=1_000,
        #     output_tokens=200,
        # )
        # out_file = tmp_path / "costs.json"
        # tracker.save(out_file)
        # assert out_file.exists()
        # data = json.loads(out_file.read_text())
        # assert "reporter" in data or "agents" in data
        # assert "total_usd" in data
