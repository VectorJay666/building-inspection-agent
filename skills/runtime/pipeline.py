"""Orchestrate ingest → flag → rank → attach. Never call ① or ③."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from skills.runtime.attach import attach_evidence
from skills.runtime.flag import flag_anomalies
from skills.runtime.ingest import ingest_readings
from skills.runtime.rank import rank_priorities


def _empty_flag() -> dict[str, Any]:
    return {"alerts": [], "notices": []}


def _empty_rank() -> dict[str, Any]:
    return {"ranked": [], "dropped": []}


def _empty_attach() -> dict[str, Any]:
    return {"attached": [], "blocked": []}


def run_pipeline(payload: Any) -> dict[str, Any]:
    """Run layer ② on a parsed JSON value (must be an array to proceed).

    If ingest has a batch error, or ``accepted`` is empty, flag / rank / attach
    are **not** called and no downstream rows are synthesized.
    """
    ingest = ingest_readings(payload)
    result: dict[str, Any] = {
        "ingest": ingest,
        "downstream_called": False,
        "skip_reason": None,
        "flag": None,
        "rank": None,
        "attach": None,
    }

    if ingest.get("batch_error"):
        result["skip_reason"] = "batch_error"
        result["flag"] = _empty_flag()
        result["rank"] = _empty_rank()
        result["attach"] = _empty_attach()
        return result

    if not ingest["accepted"]:
        if not ingest["rejected"]:
            result["skip_reason"] = "empty_batch"
        else:
            result["skip_reason"] = "all_rejected"
        result["flag"] = _empty_flag()
        result["rank"] = _empty_rank()
        result["attach"] = _empty_attach()
        return result

    flag = flag_anomalies(ingest["accepted"])
    rank = rank_priorities(flag["alerts"])
    attach = attach_evidence(rank["ranked"])
    result["downstream_called"] = True
    result["flag"] = flag
    result["rank"] = rank
    result["attach"] = attach
    return result


def run_pipeline_from_text(text: str) -> dict[str, Any]:
    """Parse JSON text then run the pipeline. Illegal JSON does not invent a batch."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return {
            "ingest": {
                "accepted": [],
                "rejected": [],
                "batch_error": f"FAIL: illegal JSON, do not invent a batch: {exc}",
            },
            "downstream_called": False,
            "skip_reason": "illegal_json",
            "flag": _empty_flag(),
            "rank": _empty_rank(),
            "attach": _empty_attach(),
        }
    return run_pipeline(payload)


def run_pipeline_from_path(path: str | Path) -> dict[str, Any]:
    """Load a file and run the pipeline."""
    batch_path = Path(path)
    try:
        text = batch_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {
            "ingest": {
                "accepted": [],
                "rejected": [],
                "batch_error": f"FAIL: file not found: {batch_path}",
            },
            "downstream_called": False,
            "skip_reason": "file_not_found",
            "flag": _empty_flag(),
            "rank": _empty_rank(),
            "attach": _empty_attach(),
        }
    except OSError as exc:
        return {
            "ingest": {
                "accepted": [],
                "rejected": [],
                "batch_error": f"FAIL: unreadable file {batch_path}: {exc}",
            },
            "downstream_called": False,
            "skip_reason": "unreadable_file",
            "flag": _empty_flag(),
            "rank": _empty_rank(),
            "attach": _empty_attach(),
        }
    return run_pipeline_from_text(text)
