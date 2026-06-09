"""Integration tests for the full patrimonial-intel pipeline.

All external calls (Anthropic API, HTTP scrapers, Playwright, e-mail) are
mocked so these tests run fully offline without side effects.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures local to integration tests
# ---------------------------------------------------------------------------

@pytest.fixture
def pipeline_env(
    mock_anthropic_client: MagicMock,
    mock_httpx_client: MagicMock,
    tmp_path: Path,
) -> dict[str, Any]:
    """Bundle all mocks and paths needed to run the full pipeline in tests."""
    return {
        "anthropic_client": mock_anthropic_client,
        "httpx_client": mock_httpx_client,
        "output_dir": tmp_path,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFullPipeline:
    """End-to-end pipeline tests with all external I/O mocked."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_mocked_external_calls(
        self, pipeline_env: dict[str, Any], sample_raw_item: dict[str, Any]
    ):
        """Running the complete pipeline with mocked scrapers/LLM/Playwright
        must:
        - produce a PDF bytes object (or write a PDF file)
        - invoke the e-mail sending function exactly once
        - not raise any exception
        """
        pytest.skip("Full pipeline integration — agents not implemented yet")

        # Sketch (to be enabled once agents exist):
        #
        # from src.agents.chefe import Chefe
        #
        # fake_pdf = b"%PDF-1.4 fake pdf content"
        #
        # with (
        #     patch("feedparser.parse", return_value=_fake_feed([sample_raw_item])),
        #     patch("anthropic.AsyncAnthropic", return_value=pipeline_env["anthropic_client"]),
        #     patch("playwright.async_api.async_playwright") as mock_pw,
        #     patch("resend.Emails.send") as mock_email,
        # ):
        #     mock_pw.return_value.__aenter__.return_value.chromium.launch = AsyncMock(
        #         return_value=_fake_browser(fake_pdf)
        #     )
        #     chefe = Chefe(output_dir=pipeline_env["output_dir"])
        #     result = await chefe.run()
        #
        # assert result["pdf"] == fake_pdf or (pipeline_env["output_dir"] / "report.pdf").exists()
        # mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_with_empty_investigador_output(
        self, pipeline_env: dict[str, Any]
    ):
        """When the Investigador returns an empty list (no news today), the
        pipeline must terminate gracefully without generating a PDF or sending
        an e-mail, and return an appropriate status indicator."""
        pytest.skip("Full pipeline integration — agents not implemented yet")

        # from src.agents.chefe import Chefe, PipelineError
        # import feedparser
        #
        # empty_feed = MagicMock()
        # empty_feed.entries = []
        # empty_feed.get = lambda k, d=None: d
        #
        # with (
        #     patch("feedparser.parse", return_value=empty_feed),
        #     patch("anthropic.AsyncAnthropic", return_value=pipeline_env["anthropic_client"]),
        #     patch("resend.Emails.send") as mock_email,
        # ):
        #     chefe = Chefe(output_dir=pipeline_env["output_dir"])
        #     with pytest.raises(PipelineError, match="no items"):
        #         await chefe.run()
        #
        # mock_email.assert_not_called()
        # pdf_files = list(pipeline_env["output_dir"].glob("*.pdf"))
        # assert pdf_files == []
