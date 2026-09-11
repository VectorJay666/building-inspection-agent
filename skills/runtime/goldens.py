"""Local golden checks for G01–G03 plus G04/G05/G06/G07/G08 shapes.

Run from repo root::

    python3 -m skills.runtime.goldens
    python3 tests/run_goldens.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from skills.runtime.attach import attach_evidence
from skills.runtime.flag import flag_anomalies
from skills.runtime.pipeline import run_pipeline, run_pipeline_from_path
from skills.runtime.rank import rank_priorities
from skills.runtime.validate import repo_root

PASS = 0
FAIL = 0
ERRORS: list[str] = []


def check(cond: bool, msg: str) -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {msg}")
    else:
        FAIL += 1
        ERRORS.append(msg)
        print(f"  FAIL  {msg}")


def mock_path(name: str) -> Path:
    return repo_root() / "data" / "mock" / name


def _valid_reading(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "reading_id": "t-1",
        "sensor_or_point": "T",
        "metric": "crack_mm",
        "value": 4.2,
        "unit": "mm",
        "timestamp": "2026-09-11T08:00:00Z",
        "location_tag": "T",
        "building_id": "demo-building-01",
    }
    base.update(overrides)
    return base


def test_g01() -> None:
    print("G01 only location A alerts; B and C stay quiet")
    result = run_pipeline_from_path(mock_path("g01.json"))
    check(result["downstream_called"] is True, "G01 downstream ran on accepted readings")
    accepted_ids = [r["reading_id"] for r in result["ingest"]["accepted"]]
    check(accepted_ids == ["g01-a-crack", "g01-b-tilt", "g01-c-crack"], "G01 all three accepted")
    check(result["ingest"]["rejected"] == [], "G01 no rejections")
    alerts = result["flag"]["alerts"]
    check(len(alerts) == 1, f"G01 exactly one alert (got {len(alerts)})")
    if alerts:
        check(alerts[0]["location_tag"] == "A", "G01 alert location is A")
        check(alerts[0]["reading_id"] == "g01-a-crack", "G01 alert is g01-a-crack")
        check(alerts[0]["rule_id"] == "rule.crack_mm.gt_3", "G01 rule_id not invented")
        check(alerts[0]["threshold"] == 3, "G01 crack threshold is 3")
    alert_locs = {a["location_tag"] for a in alerts}
    check("B" not in alert_locs and "C" not in alert_locs, "G01 B and C do not alert")
    ranked_locs = [r["location_tag"] for r in result["rank"]["ranked"]]
    check(ranked_locs == ["A"], "G01 ranked list is only A")
    attached_locs = [e["location_tag"] for e in result["attach"]["attached"]]
    check(attached_locs == ["A"], "G01 evidence only for A")
    check(result["attach"]["blocked"] == [], "G01 nothing blocked")
    if result["attach"]["attached"]:
        ev = result["attach"]["attached"][0]
        check(
            ev["conclusion"] == "crack_mm 4.2 > 3 (rule.crack_mm.gt_3)",
            f"G01 grounded conclusion (got {ev['conclusion']!r})",
        )
        check(ev["confidence"] == 1.0, "G01 confidence 1.0")


def test_g02() -> None:
    print("G02 only the tilt alerts and has a recheck task")
    result = run_pipeline_from_path(mock_path("g02.json"))
    alerts = result["flag"]["alerts"]
    check(len(alerts) == 1, f"G02 exactly one alert (got {len(alerts)})")
    if alerts:
        check(alerts[0]["metric"] == "tilt_deg", "G02 metric is tilt_deg")
        check(alerts[0]["value"] == 0.8, "G02 value 0.8")
        check(alerts[0]["threshold"] == 0.5, "G02 tilt threshold 0.5")
        check(alerts[0]["rule_id"] == "rule.tilt_deg.gt_0_5", "G02 rule_id")
        check(alerts[0]["location_tag"] == "P1", "G02 location P1")
    ranked = result["rank"]["ranked"]
    check(len(ranked) == 1, "G02 one ranked item")
    if ranked:
        check(ranked[0]["recheck_task"] == "recheck:P1:tilt_deg", "G02 recheck:P1:tilt_deg")
    check(len(result["attach"]["attached"]) == 1, "G02 evidence attached")
    if result["attach"]["attached"]:
        ev = result["attach"]["attached"][0]
        check(
            ev["conclusion"] == "tilt_deg 0.8 > 0.5 (rule.tilt_deg.gt_0_5)",
            f"G02 conclusion (got {ev['conclusion']!r})",
        )


def test_g03() -> None:
    print("G03 two alerts; E-corner before N-wall; stable across two runs")
    first = run_pipeline_from_path(mock_path("g03.json"))
    second = run_pipeline_from_path(mock_path("g03.json"))
    alerts = first["flag"]["alerts"]
    check(len(alerts) == 2, f"G03 two alerts (got {len(alerts)})")
    order = [r["location_tag"] for r in first["rank"]["ranked"]]
    check(order == ["E-corner", "N-wall"], f"G03 rank order E-corner then N-wall (got {order})")
    order2 = [r["location_tag"] for r in second["rank"]["ranked"]]
    check(order == order2, "G03 rank order identical on repeat")
    conc1 = [e["conclusion"] for e in first["attach"]["attached"]]
    conc2 = [e["conclusion"] for e in second["attach"]["attached"]]
    check(conc1 == conc2, "G03 conclusions identical on repeat")
    check(len(first["rank"]["ranked"]) == 2, "G03 two ranked items")
    if len(first["rank"]["ranked"]) == 2:
        check(
            first["rank"]["ranked"][0]["recheck_task"] == "recheck:E-corner:tilt_deg",
            "G03 #1 recheck E-corner tilt",
        )
        check(
            first["rank"]["ranked"][1]["recheck_task"] == "recheck:N-wall:crack_mm",
            "G03 #2 recheck N-wall crack",
        )
    dump1 = json.dumps(first["attach"]["attached"], sort_keys=True)
    dump2 = json.dumps(second["attach"]["attached"], sort_keys=True)
    check(dump1 == dump2, "G03 attached evidence JSON identical on repeat")


def test_g04_empty_batch() -> None:
    print("G04 empty batch [] — no invented downstream")
    result = run_pipeline([])
    check(result["ingest"]["batch_error"] is None, "G04 ingest succeeds-with-empty")
    check(result["ingest"]["accepted"] == [], "G04 no accepted readings")
    check(result["ingest"]["rejected"] == [], "G04 no rejections (nothing to reject)")
    check(result["downstream_called"] is False, "G04 flag/rank/attach not called")
    check(result["skip_reason"] == "empty_batch", "G04 skip_reason empty_batch")
    check(result["flag"]["alerts"] == [], "G04 no alerts")
    check(result["rank"]["ranked"] == [], "G04 no ranked items")
    check(result["attach"]["attached"] == [], "G04 no evidence rows")
    check(result["attach"]["blocked"] == [], "G04 no fake BLOCKs")


def test_g05_missing_value() -> None:
    print("G05 missing value rejected at ingest; sibling may proceed")
    sibling = _valid_reading(
        reading_id="g05-ok",
        sensor_or_point="OK",
        location_tag="OK",
        metric="tilt_deg",
        value=0.8,
        unit="deg",
    )
    bad = _valid_reading(reading_id="g05-missing-value", location_tag="BAD")
    del bad["value"]
    result = run_pipeline([bad, sibling])
    rejected = result["ingest"]["rejected"]
    accepted_ids = [r["reading_id"] for r in result["ingest"]["accepted"]]
    check(len(rejected) == 1, f"G05 one rejection (got {len(rejected)})")
    if rejected:
        check(rejected[0].get("reading_id") == "g05-missing-value", "G05 rejected id")
        check(rejected[0].get("code") == "MISSING_VALUE", f"G05 code MISSING_VALUE (got {rejected[0].get('code')})")
    check("g05-missing-value" not in accepted_ids, "G05 missing-value not accepted")
    check("g05-ok" in accepted_ids, "G05 sibling accepted")
    alert_ids = [a["reading_id"] for a in result["flag"]["alerts"]]
    check("g05-missing-value" not in alert_ids, "G05 missing-value not flagged")
    check("g05-ok" in alert_ids, "G05 sibling over-threshold still alerts")


def test_g06_attach_block() -> None:
    print("G06 missing threshold/rule_id at attach → BLOCK")
    incomplete = {
        "reading_id": "g06-faulty",
        "sensor_or_point": "X",
        "metric": "crack_mm",
        "value": 9.0,
        "timestamp": "2026-09-11T08:00:00Z",
        "location_tag": "X",
        # threshold and rule_id omitted on purpose (faulty flag)
    }
    ranked_drop = rank_priorities([incomplete])
    check(ranked_drop["ranked"] == [], "G06 rank drops incomplete alert")
    check(len(ranked_drop["dropped"]) == 1, "G06 drop is explicit")
    if ranked_drop["dropped"]:
        missing = set(ranked_drop["dropped"][0].get("missing_fields") or [])
        check("threshold" in missing and "rule_id" in missing, "G06 rank lists missing threshold+rule_id")

    attach = attach_evidence([incomplete])
    check(attach["attached"] == [], "G06 no attached chain")
    check(len(attach["blocked"]) == 1, "G06 explicit BLOCK")
    if attach["blocked"]:
        block = attach["blocked"][0]
        check(block.get("status") == "blocked", "G06 status blocked")
        missing = set(block.get("missing_fields") or [])
        check("threshold" in missing and "rule_id" in missing, "G06 BLOCK lists missing fields")
        check("conclusion" not in incomplete, "G06 did not invent conclusion on input")


def test_g07_unknown_metric() -> None:
    print("G07 unknown metric — no invented threshold")
    humidity = _valid_reading(
        reading_id="g07-humidity",
        metric="humidity_pct",
        value=80,
        unit="pct",
        location_tag="H",
    )
    result = run_pipeline([humidity])
    rejected = result["ingest"]["rejected"]
    check(len(rejected) == 1, "G07 ingest rejects unknown metric (schema enum)")
    if rejected:
        check(rejected[0].get("code") == "UNKNOWN_METRIC", f"G07 code (got {rejected[0].get('code')})")
    check(result["downstream_called"] is False, "G07 all-rejected: no downstream")
    check(result["flag"]["alerts"] == [], "G07 no alerts")

    # If a reading slips past ingest, flag must still not invent a rule.
    slipped = flag_anomalies([humidity])
    check(slipped["alerts"] == [], "G07 flag produces no alert for humidity_pct")
    codes = [n.get("code") for n in slipped["notices"]]
    check("UNKNOWN_METRIC" in codes, "G07 flag records UNKNOWN_METRIC")


def test_g08_repeat_identity() -> None:
    print("G08 same G01 batch twice → identical rank and conclusions")
    a = run_pipeline_from_path(mock_path("g01.json"))
    b = run_pipeline_from_path(mock_path("g01.json"))
    rank_a = [(r["rank"], r["reading_id"], r["recheck_task"]) for r in a["rank"]["ranked"]]
    rank_b = [(r["rank"], r["reading_id"], r["recheck_task"]) for r in b["rank"]["ranked"]]
    check(rank_a == rank_b, "G08 identical rank")
    conc_a = [e["conclusion"] for e in a["attach"]["attached"]]
    conc_b = [e["conclusion"] for e in b["attach"]["attached"]]
    check(conc_a == conc_b, "G08 identical conclusions")
    check(
        json.dumps(a["attach"]["attached"], sort_keys=True)
        == json.dumps(b["attach"]["attached"], sort_keys=True),
        "G08 identical evidence JSON",
    )


def test_equality_is_not_alert() -> None:
    print("boundary: equality does not alert")
    batch = [
        _valid_reading(
            reading_id="eq-crack",
            metric="crack_mm",
            value=3,
            unit="mm",
            location_tag="EQ-C",
            sensor_or_point="EQ-C",
        ),
        _valid_reading(
            reading_id="eq-tilt",
            metric="tilt_deg",
            value=0.5,
            unit="deg",
            location_tag="EQ-T",
            sensor_or_point="EQ-T",
        ),
    ]
    result = run_pipeline(batch)
    check(len(result["ingest"]["accepted"]) == 2, "equality readings accepted")
    check(result["flag"]["alerts"] == [], "value == threshold does not alert")


def test_non_array_and_illegal_json() -> None:
    print("batch errors are loud; no invented array")
    obj = run_pipeline({"readings": []})
    check(obj["ingest"]["batch_error"] is not None, "object payload fails the batch")
    check(obj["downstream_called"] is False, "object payload does not call downstream")
    check(obj["ingest"]["accepted"] == [], "object payload does not invent accepted")

    from skills.runtime.pipeline import run_pipeline_from_text

    bad = run_pipeline_from_text("{not json")
    check(bad["skip_reason"] == "illegal_json", "illegal JSON skip_reason")
    check(bad["downstream_called"] is False, "illegal JSON does not call downstream")


def main() -> int:
    print("building-inspection-agent goldens (layer ②)")
    test_g01()
    test_g02()
    test_g03()
    test_g04_empty_batch()
    test_g05_missing_value()
    test_g06_attach_block()
    test_g07_unknown_metric()
    test_g08_repeat_identity()
    test_equality_is_not_alert()
    test_non_array_and_illegal_json()
    print()
    print(f"{PASS} passed, {FAIL} failed")
    if ERRORS:
        print("failures:")
        for msg in ERRORS:
            print(f"  - {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
