#!/usr/bin/env python3
"""Download official GPQA Diamond after the user has accepted dataset terms."""

from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


GPQA_DIAMOND_URL = "https://huggingface.co/datasets/Idavidrein/gpqa/resolve/main/gpqa_diamond.csv"


def load_token(explicit_token: str | None) -> str:
    if explicit_token:
        return explicit_token.strip()
    env_token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
    if env_token:
        return env_token.strip()
    for path in [
        Path.home() / ".cache/huggingface/token",
        Path.home() / ".huggingface/token",
    ]:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/private/gpqa_diamond.csv")
    parser.add_argument("--token", default=None)
    args = parser.parse_args()

    token = load_token(args.token)
    if not token:
        print(
            "Missing Hugging Face token. Accept the GPQA dataset terms, then set "
            "HUGGINGFACE_TOKEN or create ~/.cache/huggingface/token.",
            file=sys.stderr,
        )
        return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(
        GPQA_DIAMOND_URL,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}: {body}", file=sys.stderr)
        print(
            "If this is 401/403, log in to Hugging Face and accept the GPQA "
            "dataset conditions for Idavidrein/gpqa.",
            file=sys.stderr,
        )
        return 1

    out_path.write_bytes(data)
    print(f"wrote {out_path} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
