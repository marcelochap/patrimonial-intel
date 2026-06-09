from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic
from loguru import logger
from playwright.async_api import async_playwright

from src.utils.cost_tracker import CostTracker

BASE_DIR = Path(__file__).parent.parent.parent
RAW_DIR = BASE_DIR / "outputs" / "raw"
REPORTS_DIR = BASE_DIR / "outputs" / "reports"

_SONNET_MODEL = "claude-sonnet-4-6"
_AGENT_NAME = "design"
_MAX_TOKENS = 8192

_HTML_PROMPT_TEMPLATE = """\
Você é um designer editorial especializado em relatórios jurídicos executivos. Gere um HTML completo e auto-contido (CSS inline ou em <style>) para um relatório PDF A4 com o seguinte conteúdo:

REGRAS DE DESIGN:
- Fonte: sistema (Arial/Helvetica)
- Cores: #1a1a2e (header), #16213e (tópicos), #0f3460 (destaques), #e94560 (badges)
- Itens com fact_status="speculation" devem ter badge amarelo "#f0a500" com texto "⚠ ESPECULATIVO"
- Itens com comparison_table devem ter tabela "Antes/Depois" com bordas
- Cada item: card com sombra leve, título em negrito, resumo, base legal em destaque cinza, insight estratégico em itálico, link clicável no rodapé
- Cabeçalho: "RELATÓRIO JURÍDICO PATRIMONIAL" + data + "Olá. Aqui está o seu relatório jurídico consolidado das últimas 24 horas."
- Rodapé: "Gerado automaticamente em {datetime}" + disclaimer

Retorne APENAS o HTML completo, começando com <!DOCTYPE html>.

DADOS DO RELATÓRIO:
{report_json}
"""


async def _generate_html(
    client: anthropic.AsyncAnthropic,
    tracker: CostTracker,
    report_data: dict[str, Any],
    date_str: str,
) -> str:
    report_json = json.dumps(report_data, indent=2, ensure_ascii=False)
    prompt = _HTML_PROMPT_TEMPLATE.format(
        datetime=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        report_json=report_json,
    )

    message = await client.messages.create(
        model=_SONNET_MODEL,
        max_tokens=_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    tracker.record(_AGENT_NAME, "sonnet", message.usage.input_tokens, message.usage.output_tokens)

    html_content = message.content[0].text.strip()
    if not html_content.startswith("<!DOCTYPE"):
        start = html_content.find("<!DOCTYPE")
        if start != -1:
            html_content = html_content[start:]

    return html_content


async def render_pdf(html_content: str, output_path: Path) -> Path:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(
            path=str(output_path),
            format="A4",
            margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"},
            print_background=True,
        )
        await browser.close()
    return output_path


async def run(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    input_path = Path(input_path)
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

    if output_path is None:
        output_path = REPORTS_DIR / f"report_{date_str}.pdf"
    output_path = Path(output_path)

    report_data: dict[str, Any] = json.loads(input_path.read_text(encoding="utf-8"))

    tracker = CostTracker()
    client = anthropic.AsyncAnthropic()

    logger.info("[design] Generating HTML via LLM")
    html_content = await _generate_html(client, tracker, report_data, date_str)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"[design] Rendering PDF to {output_path}")
    await render_pdf(html_content, output_path)

    pdf_size = output_path.stat().st_size if output_path.exists() else 0
    if pdf_size == 0:
        raise RuntimeError(f"[design] PDF rendered but is empty: {output_path}")

    logger.info(f"[design] PDF saved to {output_path} ({pdf_size} bytes)")

    cost_path = tracker.save()
    logger.info(f"[design] Cost report saved to {cost_path}")

    return output_path


async def main() -> None:
    import sys

    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    if len(sys.argv) < 2:
        input_path = RAW_DIR / f"validador_{date_str}.json"
    else:
        input_path = Path(sys.argv[1])

    result = await run(input_path)
    print(f"Output: {result}")


if __name__ == "__main__":
    asyncio.run(main())
