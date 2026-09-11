#!/usr/bin/env python3
"""Layer ② mock loop: ingest → flag → rank → attach on a JSON batch.

Usage:
  python3 demo/run_mock_loop.py data/mock/g01.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.runtime.pipeline import run_pipeline_from_path  # noqa: E402
from skills.runtime.rules import format_number  # noqa: E402


def _print_json(label: str, obj: object) -> None:
    print(f"{label}:")
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _summarize_reading(item: dict) -> str:
    loc = item.get("location_tag", "?")
    metric = item.get("metric", "?")
    value = item.get("value", "?")
    rid = item.get("reading_id", "?")
    return f"{rid} location={loc} {metric}={value}"


def render(path: Path, result: dict) -> None:
    print("building-inspection-agent · mock loop (layer ② runtime)")
    print(f"batch: {path}")
    print("pipeline: ingest_readings → flag_anomalies → rank_priorities → attach_evidence")
    print("v0 locks ② engine only; do not run ① decision or ③ export")
    print("evidence: missing any required field → attach_evidence BLOCK")
    print("gate: 0 SILENT_FAIL")
    print()

    ingest = result["ingest"]
    batch_error = ingest.get("batch_error")
    if batch_error:
        print(batch_error)
        print("downstream skills NOT called (no invented readings)")
        return

    accepted = ingest["accepted"]
    rejected = ingest["rejected"]
    print(f"ingest accepted={len(accepted)} rejected={len(rejected)}")
    if accepted:
        for item in accepted:
            print(f"  accepted  {_summarize_reading(item)}")
    if rejected:
        for rec in rejected:
            rid = rec.get("reading_id", "(no reading_id)")
            print(f"  rejected  index={rec.get('index')} {rid} [{rec.get('code')}] {rec.get('reason')}")
    if not accepted and not rejected:
        print("  (empty array)")

    if not result["downstream_called"]:
        reason = result.get("skip_reason") or "no accepted readings"
        print()
        print(
            f"downstream skills NOT called ({reason}): "
            "no invented alerts, ranks, recheck tasks, or evidence rows"
        )
        flag = result["flag"]
        rank = result["rank"]
        attach = result["attach"]
        print(f"  alerts={len(flag['alerts'])} ranked={len(rank['ranked'])} "
              f"attached={len(attach['attached'])} blocked={len(attach['blocked'])}")
        return

    flag = result["flag"]
    alerts = flag["alerts"]
    notices = flag["notices"]
    print()
    print(f"flag alerts={len(alerts)} notices={len(notices)}")
    if not alerts:
        print("  (no over-threshold alerts)")
    for alert in alerts:
        print(
            "  ALERT  "
            f"location={alert['location_tag']} "
            f"{alert['metric']} {format_number(alert['value'])} > "
            f"{format_number(alert['threshold'])} "
            f"({alert['rule_id']}) reading_id={alert['reading_id']}"
        )
    for notice in notices:
        rid = notice.get("reading_id", "")
        print(f"  NOTICE [{notice.get('code')}] {rid} {notice.get('reason')}")

    accepted_ids = {item.get("reading_id") for item in accepted}
    alert_ids = {alert.get("reading_id") for alert in alerts}
    quiet = [item for item in accepted if item.get("reading_id") not in alert_ids]
    if quiet:
        print("  not alerting (under-threshold or notice):")
        for item in quiet:
            print(f"    {_summarize_reading(item)}")

    rank = result["rank"]
    ranked = rank["ranked"]
    dropped = rank["dropped"]
    print()
    print(f"rank ranked={len(ranked)} dropped={len(dropped)}")
    for item in ranked:
        print(
            f"  #{item['rank']} location={item['location_tag']} "
            f"{item['metric']} recheck={item['recheck_task']} "
            f"reading_id={item['reading_id']}"
        )
    for rec in dropped:
        print(f"  DROP [{rec.get('code')}] {rec.get('reason')}")

    attach = result["attach"]
    attached = attach["attached"]
    blocked = attach["blocked"]
    print()
    print(f"attach attached={len(attached)} blocked={len(blocked)}")
    for item in attached:
        print(
            f"  ATTACHED location={item['location_tag']} "
            f"conclusion={item['conclusion']!r} confidence={item['confidence']}"
        )
    for rec in blocked:
        print(f"  BLOCK {rec.get('reason')}")

    if attached:
        print()
        _print_json("evidence chain", attached)
    if blocked:
        print()
        _print_json("blocked", blocked)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 demo/run_mock_loop.py <batch.json>", file=sys.stderr)
        return 2

    batch_path = Path(argv[1])
    result = run_pipeline_from_path(batch_path)
    render(batch_path, result)

    ingest = result["ingest"]
    if ingest.get("batch_error"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
