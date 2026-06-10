from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Any

import anthropic
from loguru import logger

from src.utils.cost_tracker import CostTracker

_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 600
_AGENT_NAME = "reporter"

_PROMPT_TEMPLATE = """\
Você é um Consultor Jurídico de Inteligência Patrimonial. Analise a notícia abaixo e retorne um JSON com:
- "summary": resumo técnico-jurídico em 3-5 linhas, linguagem clara para gestor de patrimônio
- "legal_basis": artigos de lei, súmulas ou número de processo mencionados. null se não houver.
- "strategic_insight": impacto real para quem possui holdings familiares ou seguros de alta renda. Máximo 3 linhas.
- "comparison_table": {{"before": "...", "after": "..."}} SOMENTE se houver mudança de entendimento ou lei. null caso contrário.

REGRAS:
- Não invente informações. Use apenas o que está no título e snippet.
- Se a base legal não estiver explícita, retorne null em legal_basis.
- Retorne APENAS o JSON, sem markdown, sem texto extra.

Notícia:
Título: {title}
Fonte: {source}
Data: {date}
Snippet: {snippet}
"""

_FALLBACK_FIELDS: dict[str, Any] = {
    "summary": None,
    "legal_basis": None,
    "strategic_insight": "Não foi possível processar.",
    "comparison_table": None,
}


def _build_prompt(item: dict[str, Any]) -> str:
    return _PROMPT_TEMPLATE.format(
        title=item.get("title", ""),
        source=item.get("source", ""),
        date=item.get("date", ""),
        snippet=item.get("snippet", ""),
    )


def _parse_llm_response(text: str) -> dict[str, Any]:
    return json.loads(text.strip())


async def _call_llm(
    client: anthropic.AsyncAnthropic,
    prompt: str,
) -> tuple[dict[str, Any], int, int]:
    message = await client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    parsed = _parse_llm_response(raw)
    return parsed, input_tokens, output_tokens


async def _process_item(
    client: anthropic.AsyncAnthropic,
    tracker: CostTracker,
    item: dict[str, Any],
) -> dict[str, Any]:
    prompt = _build_prompt(item)

    try:
        fields, inp, out = await _call_llm(client, prompt)
        tracker.record(_AGENT_NAME, "sonnet", inp, out)
    except (json.JSONDecodeError, KeyError, IndexError):
        logger.warning("JSON inválido na 1ª tentativa para '{}', retentando...", item.get("title", ""))
        try:
            fields, inp, out = await _call_llm(client, prompt)
            tracker.record(_AGENT_NAME, "sonnet", inp, out)
        except Exception as exc:
            logger.error("Falha definitiva ao processar item '{}': {}", item.get("title", ""), exc)
            fallback = dict(_FALLBACK_FIELDS)
            fallback["summary"] = item.get("snippet", "")
            return {**item, **fallback}
    except Exception as exc:
        logger.error("Erro inesperado ao processar item '{}': {}", item.get("title", ""), exc)
        fallback = dict(_FALLBACK_FIELDS)
        fallback["summary"] = item.get("snippet", "")
        return {**item, **fallback}

    return {**item, **fields}


async def _process_topic(
    client: anthropic.AsyncAnthropic,
    tracker: CostTracker,
    topic_label: str,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in items:
        processed = await _process_item(client, tracker, item)
        results.append(processed)
        await asyncio.sleep(0.5)
    logger.info("Tópico '{}' processado: {} itens.", topic_label, len(results))
    return results


async def run(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    input_path = Path(input_path)
    if output_path is None:
        today = date.today().isoformat()
        output_path = Path("outputs") / "raw" / f"reporter_{today}.json"
    output_path = Path(output_path)

    envelope: dict[str, Any] = json.loads(input_path.read_text(encoding="utf-8"))
    # Support both flat {topic: [items]} and wrapped {"topics": {topic: [items]}, ...}
    topics_data: dict[str, list[dict[str, Any]]] = envelope.get("topics", envelope)

    tracker = CostTracker()
    client = anthropic.AsyncAnthropic()

    topic_tasks = {
        topic: _process_topic(client, tracker, topic, items)
        for topic, items in topics_data.items()
        if isinstance(items, list)
    }

    results_per_topic = await asyncio.gather(*topic_tasks.values())
    output_data: dict[str, list[dict[str, Any]]] = dict(
        zip(topic_tasks.keys(), results_per_topic)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Reporter concluído. Arquivo salvo em '{}'.", output_path)

    cost_path = tracker.save()
    logger.info("Custo registrado em '{}'.", cost_path)

    return output_path


async def main() -> None:
    import sys

    if len(sys.argv) < 2:
        today = date.today().isoformat()
        input_path = Path("outputs") / "raw" / f"investigador_{today}.json"
    else:
        input_path = Path(sys.argv[1])

    result = await run(input_path)
    print(f"Output: {result}")


if __name__ == "__main__":
    asyncio.run(main())
