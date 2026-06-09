from __future__ import annotations

import asyncio
import difflib
import json
from datetime import date
from pathlib import Path
from typing import Any

import anthropic
from loguru import logger

from src.utils.cost_tracker import CostTracker

_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 1024
_AGENT_NAME = "curador"
_TOP_N = 3
_SIMILARITY_THRESHOLD = 0.80

_SOURCE_HIERARCHY: dict[str, int] = {
    "stf": 0,
    "stj": 0,
    "dou": 0,
    "conjur": 1,
    "migalhas": 1,
    "jota": 1,
}

_SCORING_PROMPT_TEMPLATE = """\
Você é um curador de inteligência jurídico-patrimonial. Avalie os itens abaixo e atribua um score de 0.0 a 1.0 para cada um, considerando:
- Impacto prático para gestão de patrimônio familiar/empresarial
- Abrangência (quantos contribuintes/famílias afeta)
- Novidade (decisão nova vs. repercussão de algo já conhecido)
- Aplicabilidade direta para quem tem holdings ou seguros de alta renda

Retorne APENAS um JSON array:
[{{"url": "...", "score": 0.0-1.0, "reason": "1 linha explicando o score"}}]

Itens para avaliar (tópico: {topic_label}):
{items_json}
"""


def _source_rank(item: dict[str, Any]) -> int:
    source_lower = str(item.get("source", "")).lower()
    for keyword, rank in _SOURCE_HIERARCHY.items():
        if keyword in source_lower:
            return rank
    return 2


def _title_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_urls: set[str] = set()
    unique: list[dict[str, Any]] = []

    for item in items:
        url = item.get("url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)

        title = item.get("title", "")
        duplicate_found = False
        for kept in unique:
            if _title_similarity(title, kept.get("title", "")) > _SIMILARITY_THRESHOLD:
                kept_rank = _source_rank(kept)
                current_rank = _source_rank(item)
                if current_rank < kept_rank:
                    unique.remove(kept)
                    unique.append(item)
                duplicate_found = True
                break

        if not duplicate_found:
            unique.append(item)

    return unique


async def _score_topic(
    client: anthropic.AsyncAnthropic,
    tracker: CostTracker,
    topic_label: str,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not items:
        return []

    items_summary = [
        {"url": it.get("url", ""), "title": it.get("title", ""), "summary": it.get("summary", it.get("snippet", ""))}
        for it in items
    ]

    prompt = _SCORING_PROMPT_TEMPLATE.format(
        topic_label=topic_label,
        items_json=json.dumps(items_summary, ensure_ascii=False, indent=2),
    )

    try:
        message = await client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        tracker.record(_AGENT_NAME, "sonnet", message.usage.input_tokens, message.usage.output_tokens)
        scores: list[dict[str, Any]] = json.loads(message.content[0].text.strip())
    except Exception as exc:
        logger.error("Falha no scoring do tópico '{}': {}", topic_label, exc)
        scores = [{"url": it.get("url", ""), "score": 0.5, "reason": "score padrão por falha no LLM"} for it in items]

    score_map: dict[str, dict[str, Any]] = {s["url"]: s for s in scores}

    enriched: list[dict[str, Any]] = []
    for item in items:
        url = item.get("url", "")
        score_entry = score_map.get(url, {"score": 0.0, "reason": ""})
        enriched.append({**item, "_score": score_entry.get("score", 0.0), "_score_reason": score_entry.get("reason", "")})

    enriched.sort(key=lambda x: x["_score"], reverse=True)
    return enriched[:_TOP_N]


async def run(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    input_path = Path(input_path)
    if output_path is None:
        today = date.today().isoformat()
        output_path = Path("outputs") / "raw" / f"curador_{today}.json"
    output_path = Path(output_path)

    reporter_data: dict[str, list[dict[str, Any]]] = json.loads(
        input_path.read_text(encoding="utf-8")
    )

    tracker = CostTracker()
    client = anthropic.AsyncAnthropic()

    deduped: dict[str, list[dict[str, Any]]] = {}
    for topic, items in reporter_data.items():
        before = len(items)
        deduped[topic] = _deduplicate(items)
        after = len(deduped[topic])
        logger.info("Tópico '{}': {} → {} itens após deduplicação.", topic, before, after)

    scoring_tasks = {
        topic: _score_topic(client, tracker, topic, items)
        for topic, items in deduped.items()
    }

    scored_results = await asyncio.gather(*scoring_tasks.values())
    output_data: dict[str, list[dict[str, Any]]] = dict(
        zip(scoring_tasks.keys(), scored_results)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Curador concluído. Arquivo salvo em '{}'.", output_path)

    cost_path = tracker.save()
    logger.info("Custo registrado em '{}'.", cost_path)

    return output_path


async def main() -> None:
    import sys

    if len(sys.argv) < 2:
        today = date.today().isoformat()
        input_path = Path("outputs") / "raw" / f"reporter_{today}.json"
    else:
        input_path = Path(sys.argv[1])

    result = await run(input_path)
    print(f"Output: {result}")


if __name__ == "__main__":
    asyncio.run(main())
