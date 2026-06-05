#!/usr/bin/env python3
"""Create a public, aggregate-only summary from a private GPQA run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, help="Private run directory")
    parser.add_argument("--out", required=True, help="Public JSON summary path")
    args = parser.parse_args()

    run_dir = Path(args.run)
    summary_path = run_dir / "summary_private.json"
    if not summary_path.exists():
        raise SystemExit(f"missing {summary_path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    public = {
        "model_label": summary["model_label"],
        "limit": summary["limit"],
        "seed": summary["seed"],
        "started_utc": summary["started_utc"],
        "ended_utc": summary["ended_utc"],
        "wall_time_sec": summary["wall_time_sec"],
        "attempted": summary["attempted"],
        "correct": summary["correct"],
        "failed": summary["failed"],
        "accuracy": summary["accuracy"],
        "avg_elapsed_sec_per_item": summary["avg_elapsed_sec_per_item"],
        "avg_predicted_tokens_per_second": summary["avg_predicted_tokens_per_second"],
        "privacy_note": summary["privacy_note"],
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
