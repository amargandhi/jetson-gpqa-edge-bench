# Methodology

## What This Measures

This harness measures a practical edge question:

> On the same 8GB Jetson Orin Nano Super running WendyOS, how much accuracy do we get per minute from Gemma 4 12B Q3 versus InstinctRazor 122B?

It is intentionally not framed as a replacement for official GPQA leaderboard scores.

## Why GPQA-Diamond

GPQA-Diamond is a hard multiple-choice science reasoning benchmark. It is useful here because:

- the answer can be scored mechanically,
- the response can be constrained to one letter,
- it is hard enough that a 122B MoE may separate from a 12B model,
- it is one of the reported benchmark families for Qwen3.5-122B-A10B / InstinctRazor.

## Privacy And Benchmark Hygiene

The official GPQA dataset is gated and asks users not to reveal examples.

This repo therefore does not store:

- questions,
- answer choices,
- explanations,
- answer keys,
- raw model completions that could echo question text.

Private raw runs are written under:

```text
runs/private/
```

Public summaries contain only aggregate statistics.

## Prompt Shape

Each item is converted into a shuffled A/B/C/D multiple-choice prompt.

Choice shuffling is deterministic using:

- the user-provided seed,
- the record ID when present,
- otherwise the row index.

Subset selection should use `--shuffle-rows` so the first public demo is a deterministic shuffled subset rather than the first rows in the CSV.

The model is instructed to answer with one letter only.

## Recommended First Run

Start with `n=20`.

Why:

- Gemma should finish quickly.
- InstinctRazor on this Jetson is expected to be very slow.
- A small subset gives us first useful latency and reliability data before attempting full `n=198`.

If the InstinctRazor run is stable, scale to:

```text
n=50
n=100
n=198
```

## How To Compare To Published Results

Do not claim equivalence unless the setup matches the original evaluation harness.

Careful phrasing:

```text
Qwen reports 86.6 on GPQA-Diamond for Qwen3.5-122B-A10B.
General Instinct has publicly reported about 80.8 for the InstinctRazor GGUF on GPQA-Diamond.
This repo measures a same-hardware Jetson subset run to see whether that direction survives under 8GB unified-memory constraints.
```
