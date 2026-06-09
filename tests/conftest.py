"""Shared fixtures for the patrimonial-intel test suite."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Raw item — output of Investigador (no summary / fact_status)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_raw_item() -> dict[str, Any]:
    return {
        "title": "STF decide sobre tributação de holdings familiares",
        "date": "2026-06-09T08:00:00+00:00",
        "url": "https://portal.stf.jus.br/noticias/verNoticiaDetalhe.asp?idConteudo=123456",
        "source": "stf",
        "topic": "1",
        "snippet": (
            "O Supremo Tribunal Federal concluiu julgamento sobre a incidência de "
            "ITCMD em holdings familiares, fixando tese de repercussão geral."
        ),
        "link_status": "verified",
    }


# ---------------------------------------------------------------------------
# Reported item — output of Reporter (adds summary / legal_basis / strategic_insight)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_reported_item(sample_raw_item: dict[str, Any]) -> dict[str, Any]:
    return {
        **sample_raw_item,
        "summary": (
            "O STF, por maioria, firmou que holdings familiares constituídas "
            "exclusivamente para planejamento patrimonial estão sujeitas ao ITCMD "
            "sobre o acervo integralizado."
        ),
        "legal_basis": "Art. 155, I, CF/88; RE 1.425.609 (Tema 1.369)",
        "strategic_insight": (
            "Famílias com holdings devem revisar cláusulas de integralização para "
            "reduzir exposição ao ITCMD antes da publicação do acórdão."
        ),
        "comparison_table": {
            "before": "Integralizações tratadas como operações societárias isentas de ITCMD",
            "after": "ITCMD incide sobre o valor dos bens integralizados em holdings familiares",
        },
    }


# ---------------------------------------------------------------------------
# Curated items — list of 3 items per topic after Curador scoring
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_curated_items(sample_reported_item: dict[str, Any]) -> list[dict[str, Any]]:
    base = sample_reported_item
    items = []
    for i in range(3):
        item = {
            **base,
            "title": f"{base['title']} — variação {i + 1}",
            "url": f"{base['url']}&v={i + 1}",
            "score": 0.9 - i * 0.1,
        }
        items.append(item)
    return items


# ---------------------------------------------------------------------------
# Validated items — list after Validador adds fact_status / fact_confidence
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_validated_items(sample_curated_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    statuses = ["fact", "opinion", "speculation"]
    result = []
    for item, status in zip(sample_curated_items, statuses):
        result.append({
            **item,
            "fact_status": status,
            "fact_confidence": 0.95 if status == "fact" else 0.65,
        })
    return result


# ---------------------------------------------------------------------------
# Mock Anthropic async client
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """Returns a MagicMock that mimics anthropic.AsyncAnthropic.

    ``client.messages.create`` is an AsyncMock that returns a pre-built
    response object with a single TextBlock.
    """
    text_block = MagicMock()
    text_block.text = (
        '{"summary": "Resumo gerado pelo LLM.", '
        '"legal_basis": "Art. 155 CF/88", '
        '"strategic_insight": "Revisar estrutura patrimonial.", '
        '"comparison_table": null}'
    )

    response = MagicMock()
    response.content = [text_block]
    response.usage = MagicMock(input_tokens=500, output_tokens=200)
    response.model = "claude-sonnet-4-6"

    messages_ns = MagicMock()
    messages_ns.create = AsyncMock(return_value=response)

    client = MagicMock()
    client.messages = messages_ns
    return client


# ---------------------------------------------------------------------------
# Mock httpx async client
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Returns a MagicMock that mimics httpx.AsyncClient.

    HEAD requests to any URL return 200 by default.
    """
    response_200 = MagicMock()
    response_200.status_code = 200

    client = MagicMock()
    client.head = AsyncMock(return_value=response_200)
    client.get = AsyncMock(return_value=response_200)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client
