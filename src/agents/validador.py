from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic
from loguru import logger

from src.utils.cost_tracker import CostTracker
from src.utils.link_validator import validate_links

BASE_DIR = Path(__file__).parent.parent.parent
RAW_DIR = BASE_DIR / "outputs" / "raw"

_HAIKU_MODEL = "claude-haiku-4-5-20251001"
_AGENT_NAME = "validador"

_SPECULATION_PHRASES = [
    "poderia",
    "teria",
    "seria",
    "especula-se",
    "segundo fontes",
    "pode vir a",
    "tende a",
    "expectativa é",
    "provável que",
    "estaria",
    "cogita-se",
]

_LLM_PROMPT_TEMPLATE = (
    "Classifique esta notícia jurídica como 'fact', 'speculation' ou 'opinion'. "
    "Retorne JSON: {{\"classification\": \"fact|speculation|opinion\", "
    "\"confidence\": 0.0-1.0, \"reason\": \"1 linha\"}}. "
    "Notícia: {title} | {snippet}"
)


def _heuristic_check(item: dict[str, Any]) -> tuple[str | None, float]:
    text = (
        item.get("title", "") + " "
        + item.get("snippet", "") + " "
        + item.get("summary", "")
    ).lower()

    matches = sum(1 for phrase in _SPECULATION_PHRASES if phrase in text)

    if matches >= 2:
        return "speculation", 0.9
    if matches == 1:
        return None, 0.5
    return "fact", 0.95


async def _llm_classify(
    client: anthropic.AsyncAnthropic,
    tracker: CostTracker,
    item: dict[str, Any],
) -> tuple[str, float]:
    prompt = _LLM_PROMPT_TEMPLATE.format(
        title=item.get("title", ""),
        snippet=item.get("snippet", ""),
    )
    try:
        message = await client.messages.create(
            model=_HAIKU_MODEL,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        tracker.record(_AGENT_NAME, "haiku", message.usage.input_tokens, message.usage.output_tokens)
        parsed: dict[str, Any] = json.loads(raw)
        classification = parsed.get("classification", "fact")
        confidence = float(parsed.get("confidence", 0.7))
        return classification, confidence
    except Exception as exc:
        logger.warning(f"[validador] LLM classify failed for '{item.get('title', '')}': {exc}")
        return "fact", 0.6


async def _validate_item(
    client: anthropic.AsyncAnthropic,
    tracker: CostTracker,
    item: dict[str, Any],
) -> dict[str, Any]:
    fact_status, fact_confidence = _heuristic_check(item)

    if fact_status is None:
        fact_status, fact_confidence = await _llm_classify(client, tracker, item)
    elif fact_confidence < 0.7:
        fact_status, fact_confidence = await _llm_classify(client, tracker, item)

    item["fact_status"] = fact_status
    item["fact_confidence"] = fact_confidence
    return item


async def run(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    input_path = Path(input_path)
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

    if output_path is None:
        output_path = RAW_DIR / f"validador_{date_str}.json"
    output_path = Path(output_path)

    raw: dict[str, Any] = json.loads(input_path.read_text(encoding="utf-8"))

    tracker = CostTracker()
    client = anthropic.AsyncAnthropic()

    topics: dict[str, list[dict[str, Any]]] = raw.get("topics", {})

    logger.info(f"[validador] Validating links for all items")
    all_items: list[dict[str, Any]] = [item for items in topics.values() for item in items]
    all_items = await validate_links(all_items)

    logger.info(f"[validador] Running fact/speculation heuristic + LLM on {len(all_items)} items")
    tasks = [_validate_item(client, tracker, item) for item in all_items]
    validated_items = await asyncio.gather(*tasks)

    idx = 0
    for topic_key, items in topics.items():
        count = len(items)
        topics[topic_key] = list(validated_items[idx : idx + count])
        idx += count

    total_items = sum(len(v) for v in topics.values())
    output_data: dict[str, Any] = {
        **raw,
        "topics": topics,
        "total_items": total_items,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"[validador] Output saved to {output_path} ({total_items} items)")

    cost_path = tracker.save()
    logger.info(f"[validador] Cost report saved to {cost_path}")

    return output_path


async def main() -> None:
    import sys

    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    if len(sys.argv) < 2:
        input_path = RAW_DIR / f"curador_{date_str}.json"
    else:
        input_path = Path(sys.argv[1])

    result = await run(input_path)
    print(f"Output: {result}")


if __name__ == "__main__":
    asyncio.run(main())
