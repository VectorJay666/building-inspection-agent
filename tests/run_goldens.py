#!/usr/bin/env python3
"""Run layer ② golden checks (G01–G08 fixtures under data/mock/).

Usage (from repo root):

    python3 tests/run_goldens.py
    python3 -m skills.runtime.goldens
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.runtime.goldens import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
