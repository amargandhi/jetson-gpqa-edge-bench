#!/usr/bin/env python3
"""Run a no-leak GPQA-style multiple-choice benchmark against an OpenAI API."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ANSWER_RE = re.compile(r"\b([ABCD])\b", re.IGNORECASE)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"no rows found in {path}")
    return rows


def pick(row: dict[str, str], *names: str, default: str = "") -> str:
    for name in names:
        value = row.get(name)
        if value is not None and value.strip():
            return value.strip()
    return default


def hashed_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def build_item(row: dict[str, str], index: int, seed: int) -> dict[str, object]:
    record_id = pick(row, "Record ID", "record_id", "id", default=f"row-{index}")
    question = pick(row, "Question", "question")
    correct = pick(row, "Correct Answer", "correct_answer", "answer")
    wrongs = [
        pick(row, "Incorrect Answer 1", "incorrect_answer_1"),
        pick(row, "Incorrect Answer 2", "incorrect_answer_2"),
        pick(row, "Incorrect Answer 3", "incorrect_answer_3"),
    ]

    if not question or not correct or any(not wrong for wrong in wrongs):
        raise ValueError(f"row {index} is missing required GPQA-style columns")

    choices = [{"text": correct, "correct": True}]
    choices.extend({"text": wrong, "correct": False} for wrong in wrongs)

    rng = random.Random(f"{seed}:{record_id}:{index}")
    rng.shuffle(choices)

    letters = "ABCD"
    correct_letter = ""
    rendered_choices = []
    for letter, choice in zip(letters, choices):
        rendered_choices.append(f"{letter}. {choice['text']}")
        if choice["correct"]:
            correct_letter = letter

    prompt = (
        "Answer this multiple-choice science question. "
        "Respond with only one letter: A, B, C, or D.\n\n"
        f"Question:\n{question}\n\n"
        "Choices:\n"
        + "\n".join(rendered_choices)
        + "\n\nAnswer:"
    )

    return {
        "index": index,
        "record_hash": hashed_id(record_id),
        "prompt": prompt,
        "correct_letter": correct_letter,
        "domain": pick(row, "High-level domain", "high_level_domain"),
    }


def post_chat(base_url: str, model: str, prompt: str, timeout: float, max_tokens: int) -> dict[str, object]:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are taking a multiple-choice benchmark. Do not explain. Do not show reasoning. Return only A, B, C, or D.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0,
        "chat_template_kwargs": {
            "enable_thinking": False,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_letter(text: str) -> str:
    stripped = text.strip().upper()
    if stripped in {"A", "B", "C", "D"}:
        return stripped
    match = ANSWER_RE.search(text)
    if match:
        return match.group(1).upper()
    return ""


def response_text(message: dict[str, object]) -> str:
    parts = []
    content = message.get("content")
    reasoning = message.get("reasoning_content")
    if isinstance(content, str):
        parts.append(content)
    if isinstance(reasoning, str):
        parts.append(reasoning)
    return "\n".join(parts)


def summarize(results: list[dict[str, object]], args: argparse.Namespace, started: float, ended: float) -> dict[str, object]:
    attempted = len(results)
    correct = sum(1 for item in results if item.get("is_correct") is True)
    failed = sum(1 for item in results if item.get("error"))
    elapsed_values = [float(item["elapsed_sec"]) for item in results if "elapsed_sec" in item]
    pred_speeds = [
        float(item["predicted_per_second"])
        for item in results
        if item.get("predicted_per_second") is not None
    ]

    return {
        "model_label": args.model_label,
        "model": args.model,
        "base_url": args.base_url,
        "csv_name": Path(args.csv).name,
        "limit": args.limit,
        "seed": args.seed,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "ended_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ended)),
        "wall_time_sec": round(ended - started, 3),
        "attempted": attempted,
        "correct": correct,
        "failed": failed,
        "accuracy": round(correct / attempted, 4) if attempted else None,
        "avg_elapsed_sec_per_item": round(sum(elapsed_values) / len(elapsed_values), 3)
        if elapsed_values
        else None,
        "avg_predicted_tokens_per_second": round(sum(pred_speeds) / len(pred_speeds), 4)
        if pred_speeds
        else None,
        "privacy_note": "No GPQA questions, choices, answer text, or answer keys are included in this summary.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to local GPQA Diamond CSV")
    parser.add_argument("--base-url", required=True, help="OpenAI-compatible /v1 base URL")
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-label", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260605)
    parser.add_argument("--shuffle-rows", action="store_true")
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument("--sleep", type=float, default=0)
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = read_rows(csv_path)
    indexed_rows = list(enumerate(rows))
    if args.shuffle_rows:
        random.Random(args.seed).shuffle(indexed_rows)
    selected = indexed_rows[: args.limit] if args.limit else indexed_rows

    private_results_path = out_dir / "private_results.jsonl"
    results: list[dict[str, object]] = []
    started = time.time()

    with private_results_path.open("w", encoding="utf-8") as handle:
        for position, (source_index, row) in enumerate(selected):
            item = build_item(row, index=source_index, seed=args.seed)
            result: dict[str, object] = {
                "index": item["index"],
                "position": position,
                "record_hash": item["record_hash"],
                "domain": item["domain"],
            }
            t0 = time.time()
            try:
                response = post_chat(
                    base_url=args.base_url,
                    model=args.model,
                    prompt=str(item["prompt"]),
                    timeout=args.timeout,
                    max_tokens=args.max_tokens,
                )
                elapsed = time.time() - t0
                message = response["choices"][0]["message"]
                content = response_text(message)
                predicted = extract_letter(content)
                timings = response.get("timings", {})
                usage = response.get("usage", {})

                result.update(
                    {
                        "elapsed_sec": round(elapsed, 3),
                        "predicted_letter": predicted,
                        "is_correct": predicted == item["correct_letter"],
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "prompt_per_second": timings.get("prompt_per_second"),
                        "predicted_per_second": timings.get("predicted_per_second"),
                    }
                )
            except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
                result.update(
                    {
                        "elapsed_sec": round(time.time() - t0, 3),
                        "error": type(exc).__name__,
                    }
                )

            results.append(result)
            handle.write(json.dumps(result, sort_keys=True) + "\n")
            handle.flush()

            print(
                f"{len(results)}/{len(selected)} "
                f"hash={result['record_hash']} "
                f"pred={result.get('predicted_letter', '?')} "
                f"ok={result.get('is_correct', False)} "
                f"sec={result.get('elapsed_sec')}",
                flush=True,
            )
            if args.sleep:
                time.sleep(args.sleep)

    ended = time.time()
    summary = summarize(results, args, started, ended)
    (out_dir / "summary_private.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
