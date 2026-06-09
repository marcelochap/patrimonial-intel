from __future__ import annotations

import asyncio
import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import resend
from loguru import logger

from src.agents import investigador, reporter
from src.utils.cost_tracker import CostTracker

BASE_DIR = Path(__file__).parent.parent.parent
RAW_DIR = BASE_DIR / "outputs" / "raw"
REPORTS_DIR = BASE_DIR / "outputs" / "reports"

_MIN_PDF_SIZE_BYTES = 50 * 1024


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _make_step(agent: str) -> dict[str, Any]:
    return {
        "agent": agent,
        "status": "skipped",
        "items_in": 0,
        "items_out": 0,
        "retries": 0,
        "errors": [],
    }


async def _run_with_retry(coro_factory, max_attempts: int = 3) -> Any:
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return await coro_factory()
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)
    raise last_exc


def _count_items(data: dict[str, Any]) -> int:
    topics = data.get("topics", {})
    if isinstance(topics, dict):
        return sum(len(v) for v in topics.values() if isinstance(v, list))
    return data.get("total_items", 0)


def _validate_investigador(data: dict[str, Any]) -> None:
    topics = data.get("topics", {})
    topics_with_items = sum(1 for v in topics.values() if isinstance(v, list) and len(v) >= 1)
    if topics_with_items < 1:
        raise ValueError("Investigador: no topics with items")


def _validate_reporter(data: dict[str, Any]) -> None:
    topics = data.get("topics", {})
    for topic, items in topics.items():
        for item in items:
            if not item.get("summary"):
                raise ValueError(f"Reporter: item missing summary in topic '{topic}'")


def _validate_curador(data: dict[str, Any]) -> None:
    if data.get("total_items", 0) < 1:
        raise ValueError("Curador: total_items < 1")


def _validate_validador(data: dict[str, Any]) -> None:
    topics = data.get("topics", {})
    for topic, items in topics.items():
        for item in items:
            if "fact_status" not in item:
                raise ValueError(f"Validador: item missing fact_status in topic '{topic}'")


def _validate_design(pdf_path: Path) -> None:
    if not pdf_path.exists():
        raise ValueError(f"Design: PDF not found at {pdf_path}")
    size = pdf_path.stat().st_size
    if size < _MIN_PDF_SIZE_BYTES:
        raise ValueError(f"Design: PDF too small ({size} bytes < {_MIN_PDF_SIZE_BYTES})")


def _send_report_email(date_str: str, pdf_path: Path) -> None:
    resend.api_key = os.environ["RESEND_API_KEY"]
    pdf_bytes = pdf_path.read_bytes()
    pdf_bytes_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    resend.Emails.send({
        "from": os.environ["REPORT_EMAIL_FROM"],
        "to": [os.environ["REPORT_EMAIL_TO"]],
        "subject": f"Relatório Jurídico Patrimonial — {date_str}",
        "html": "<p>Olá. Seu relatório diário está em anexo.</p>",
        "attachments": [{"filename": f"report_{date_str}.pdf", "content": pdf_bytes_b64}],
    })


def _send_error_email(date_str: str, log_data: dict[str, Any]) -> None:
    resend.api_key = os.environ["RESEND_API_KEY"]
    failed_steps = [s for s in log_data.get("steps", []) if s["status"] == "failed"]
    error_lines = "<br>".join(
        f"<b>{s['agent']}</b>: {', '.join(s['errors'])}" for s in failed_steps
    )
    resend.Emails.send({
        "from": os.environ["REPORT_EMAIL_FROM"],
        "to": [os.environ["REPORT_EMAIL_TO"]],
        "subject": f"[ERRO] Relatório Patrimonial {date_str}",
        "html": f"<p>O pipeline encontrou erros:</p>{error_lines}",
    })


async def main() -> None:
    from src.agents import curador as curador_mod
    from src.agents import validador as validador_mod
    from src.agents import design as design_mod

    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    tracker = CostTracker()

    pipeline_log: dict[str, Any] = {
        "date": date_str,
        "start_time": _now_iso(),
        "end_time": None,
        "status": "failed",
        "steps": [],
        "cost_summary": {},
    }

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    investigador_path = RAW_DIR / f"investigador_{date_str}.json"
    reporter_path = RAW_DIR / f"reporter_{date_str}.json"
    curador_path = RAW_DIR / f"curador_{date_str}.json"
    validador_path = RAW_DIR / f"validador_{date_str}.json"
    pdf_path = REPORTS_DIR / f"report_{date_str}.pdf"

    # --- Investigador ---
    step = _make_step("investigador")
    pipeline_log["steps"].append(step)
    try:
        await _run_with_retry(investigador.main, max_attempts=3)
        step["retries"] = 0

        inv_data = json.loads(investigador_path.read_text(encoding="utf-8"))
        _validate_investigador(inv_data)

        topics = inv_data.get("topics", {})
        topics_with_items = sum(1 for v in topics.values() if isinstance(v, list) and len(v) >= 1)
        step["items_out"] = _count_items(inv_data)
        step["status"] = "success"
        logger.info(f"[chefe] Investigador: {step['items_out']} items, {topics_with_items} topics with data")

        if topics_with_items < 2:
            raise ValueError(f"Investigador: only {topics_with_items} topics have items (minimum 2)")

    except Exception as exc:
        step["status"] = "failed"
        step["errors"].append(str(exc))
        logger.error(f"[chefe] Investigador failed: {exc}")
        pipeline_log["end_time"] = _now_iso()
        pipeline_log["cost_summary"] = tracker.summary()
        _save_log(pipeline_log, date_str)
        _send_error_email(date_str, pipeline_log)
        return

    # --- Reporter ---
    step = _make_step("reporter")
    pipeline_log["steps"].append(step)
    step["items_in"] = _count_items(inv_data)
    try:
        await _run_with_retry(
            lambda: reporter.run(investigador_path, reporter_path),
            max_attempts=3,
        )
        rep_data = json.loads(reporter_path.read_text(encoding="utf-8"))
        _validate_reporter(rep_data)
        step["items_out"] = _count_items(rep_data)
        step["status"] = "success"
        logger.info(f"[chefe] Reporter: {step['items_out']} items processed")
    except Exception as exc:
        step["status"] = "failed"
        step["errors"].append(str(exc))
        logger.error(f"[chefe] Reporter failed: {exc}")
        pipeline_log["end_time"] = _now_iso()
        pipeline_log["cost_summary"] = tracker.summary()
        _save_log(pipeline_log, date_str)
        _send_error_email(date_str, pipeline_log)
        return

    # --- Curador ---
    step = _make_step("curador")
    pipeline_log["steps"].append(step)
    step["items_in"] = _count_items(rep_data)
    try:
        await _run_with_retry(
            lambda: curador_mod.run(reporter_path, curador_path),
            max_attempts=3,
        )
        cur_data = json.loads(curador_path.read_text(encoding="utf-8"))
        _validate_curador(cur_data)
        step["items_out"] = _count_items(cur_data)
        step["status"] = "success"
        logger.info(f"[chefe] Curador: {step['items_out']} items after curation")
    except Exception as exc:
        step["status"] = "failed"
        step["errors"].append(str(exc))
        logger.error(f"[chefe] Curador failed: {exc}")
        pipeline_log["end_time"] = _now_iso()
        pipeline_log["cost_summary"] = tracker.summary()
        _save_log(pipeline_log, date_str)
        _send_error_email(date_str, pipeline_log)
        return

    # --- Validador ---
    step = _make_step("validador")
    pipeline_log["steps"].append(step)
    step["items_in"] = _count_items(cur_data)
    try:
        await _run_with_retry(
            lambda: validador_mod.run(curador_path, validador_path),
            max_attempts=3,
        )
        val_data = json.loads(validador_path.read_text(encoding="utf-8"))
        _validate_validador(val_data)
        step["items_out"] = _count_items(val_data)
        step["status"] = "success"
        logger.info(f"[chefe] Validador: {step['items_out']} items validated")
    except Exception as exc:
        step["status"] = "failed"
        step["errors"].append(str(exc))
        logger.error(f"[chefe] Validador failed: {exc}")
        pipeline_log["end_time"] = _now_iso()
        pipeline_log["cost_summary"] = tracker.summary()
        _save_log(pipeline_log, date_str)
        _send_error_email(date_str, pipeline_log)
        return

    # --- Design ---
    step = _make_step("design")
    pipeline_log["steps"].append(step)
    step["items_in"] = _count_items(val_data)
    try:
        await _run_with_retry(
            lambda: design_mod.run(validador_path, pdf_path),
            max_attempts=3,
        )
        _validate_design(pdf_path)
        step["items_out"] = 1
        step["status"] = "success"
        logger.info(f"[chefe] Design: PDF at {pdf_path} ({pdf_path.stat().st_size} bytes)")
    except Exception as exc:
        step["status"] = "failed"
        step["errors"].append(str(exc))
        logger.error(f"[chefe] Design failed: {exc}")
        pipeline_log["end_time"] = _now_iso()
        pipeline_log["cost_summary"] = tracker.summary()
        _save_log(pipeline_log, date_str)
        _send_error_email(date_str, pipeline_log)
        return

    # --- Email ---
    step = _make_step("email")
    pipeline_log["steps"].append(step)
    try:
        _send_report_email(date_str, pdf_path)
        step["status"] = "success"
        logger.info(f"[chefe] Email sent for {date_str}")
    except Exception as exc:
        step["status"] = "failed"
        step["errors"].append(str(exc))
        logger.error(f"[chefe] Email failed: {exc}")
        pipeline_log["status"] = "partial"
        pipeline_log["end_time"] = _now_iso()
        pipeline_log["cost_summary"] = tracker.summary()
        _save_log(pipeline_log, date_str)
        return

    pipeline_log["status"] = "success"
    pipeline_log["end_time"] = _now_iso()
    pipeline_log["cost_summary"] = tracker.summary()
    _save_log(pipeline_log, date_str)
    logger.info(f"[chefe] Pipeline completed successfully for {date_str}")


def _save_log(log: dict[str, Any], date_str: str) -> None:
    log_path = RAW_DIR / f"pipeline_log_{date_str}.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"[chefe] Pipeline log saved to {log_path}")


if __name__ == "__main__":
    asyncio.run(main())
