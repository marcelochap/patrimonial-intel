from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

ModelName = Literal["haiku", "sonnet"]

_PRICING: dict[str, dict[str, float]] = {
    # USD per 1M tokens
    "haiku":  {"input": 0.80, "output": 4.00},
    "sonnet": {"input": 3.00, "output": 15.00},
}


@dataclass
class _Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def cost(self, model: str) -> float:
        rates = _PRICING.get(model, _PRICING["sonnet"])
        return (
            self.input_tokens  * rates["input"]  / 1_000_000
            + self.output_tokens * rates["output"] / 1_000_000
        )


class CostTracker:
    def __init__(self) -> None:
        # { agent_name: { model_name: _Usage } }
        self._data: dict[str, dict[str, _Usage]] = {}

    def record(
        self,
        agent: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        agent_bucket = self._data.setdefault(agent, {})
        usage = agent_bucket.setdefault(model, _Usage())
        usage.input_tokens += input_tokens
        usage.output_tokens += output_tokens

    def summary(self) -> dict:
        agents_out: dict[str, dict] = {}
        total_usd = 0.0

        for agent, models in self._data.items():
            agent_cost = 0.0
            model_breakdown: dict[str, dict] = {}

            for model, usage in models.items():
                cost = usage.cost(model)
                agent_cost += cost
                model_breakdown[model] = {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "cost_usd": round(cost, 6),
                }

            agents_out[agent] = {
                "models": model_breakdown,
                "total_cost_usd": round(agent_cost, 6),
            }
            total_usd += agent_cost

        return {
            "agents": agents_out,
            "total_cost_usd": round(total_usd, 6),
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        }

    def save(self, path: str | None = None) -> str:
        if path is None:
            date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            path = os.path.join("outputs", "raw", f"cost_{date_str}.json")

        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(self.summary(), indent=2, ensure_ascii=False), encoding="utf-8")
        return str(dest)
