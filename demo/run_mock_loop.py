#!/usr/bin/env python3
"""Placeholder mock loop for layer ②.

Does NOT implement the Skills runtime. Prints the ingest → flag → rank → attach
path and reminds operators of the evidence / SILENT_FAIL gates.

Usage:
  python3 demo/run_mock_loop.py data/mock/g01.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SKILLS = [
    ("ingest_readings", "skills/01_ingest_readings.md"),
    ("flag_anomalies", "skills/02_flag_anomalies.md"),
    ("rank_priorities", "skills/03_rank_priorities.md"),
    ("attach_evidence", "skills/04_attach_evidence.md"),
]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 demo/run_mock_loop.py <batch.json>", file=sys.stderr)
        return 2

    batch_path = Path(argv[1])
    print("building-inspection-agent · mock loop (STUB, no runtime)")
    print(f"batch: {batch_path}")
    print("pipeline: ingest_readings → flag_anomalies → rank_priorities → attach_evidence")
    print("v0 locks ② engine only; do not run ① decision or ③ export")
    print("evidence: missing any required field → attach_evidence BLOCK")
    print("gate: 0 SILENT_FAIL")
    print()

    try:
        raw = batch_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except FileNotFoundError:
        print(f"FAIL: file not found: {batch_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"FAIL: illegal JSON, do not invent a batch: {exc}", file=sys.stderr)
        return 1

    if not isinstance(data, list):
        print("FAIL: batch must be a JSON array; entire payload rejected", file=sys.stderr)
        return 1

    print(f"parsed array length: {len(data)} (validation is TODO in ingest_readings)")
    if len(data) == 0:
        print("empty batch: do not invent readings; do not call downstream")
        return 0

    for name, stub in SKILLS:
        print(f"TODO invoke skill {name}  ({stub})")

    print()
    print("stop: Skills engineer implements the four stubs; Test wires G01–G08.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
