# Jetson GPQA Edge Bench

A small, source-respecting benchmark harness for comparing:

- `google/gemma-4-12B` via the working `unsloth/gemma-4-12b-it-GGUF` Jetson server.
- `General-Instinct/InstinctRazor-Qwen3.5-122B-A10B-GGUF` on the same Jetson/WendyOS setup.

The point is not to claim a new leaderboard score. The point is to show a useful edge demo:

> Does a very slow 122B MoE preserve any GPQA-Diamond accuracy advantage when squeezed through an 8GB unified-memory Jetson, or does the practical bottleneck dominate?

## Public-Sharing Rule

Do not commit or post GPQA questions, answer text, or answer keys.

The official GPQA dataset is gated on Hugging Face and asks users not to reveal examples. This repo is designed to publish only:

- aggregate accuracy,
- latency and throughput,
- model/runtime settings,
- non-reversible hashed item IDs if needed.

Private inputs and raw receipts live under ignored folders:

```text
data/private/
runs/private/
```

## Sources

- GPQA official dataset: https://huggingface.co/datasets/Idavidrein/gpqa
- GPQA paper: https://arxiv.org/abs/2311.12022
- Qwen3.5-122B-A10B model card: https://huggingface.co/Qwen/Qwen3.5-122B-A10B
- InstinctRazor GGUF: https://huggingface.co/General-Instinct/InstinctRazor-Qwen3.5-122B-A10B-GGUF
- Gemma 4 12B model card: https://huggingface.co/google/gemma-4-12B
- Unsloth Gemma 4 12B GGUF: https://huggingface.co/unsloth/gemma-4-12b-it-GGUF

## Reported Reference Points

Use these as context, not as direct apples-to-apples claims.

- Qwen reports `Qwen3.5-122B-A10B` at `86.6` on GPQA Diamond.
- General Instinct has publicly reported InstinctRazor GGUF around `80.8` on GPQA Diamond, `n=198`, using their llama.cpp evaluation path.
- Our Jetson text-only server tests measured Gemma 4 12B Q3 at about `5.5 tok/s` on a short bounded response.
- Our Jetson text-only InstinctRazor smoke test measured about `0.23 tok/s` on a tiny chat response.

## Setup

Accept GPQA access on Hugging Face, then place the official Diamond CSV here:

```text
data/private/gpqa_diamond.csv
```

You can download it with:

```bash
export HUGGINGFACE_TOKEN=hf_...
python3 scripts/download_gpqa.py
```

or put the token in:

```text
~/.cache/huggingface/token
```

The expected columns are the official GPQA CSV-style columns:

```text
Question
Correct Answer
Incorrect Answer 1
Incorrect Answer 2
Incorrect Answer 3
Record ID
High-level domain
Subdomain
```

## Quick Harness Test

This uses a tiny non-GPQA toy fixture to prove the runner works without leaking benchmark data.

```bash
python3 scripts/run_gpqa.py \
  --csv tests/fixtures/toy_gpqa_like.csv \
  --base-url http://192.168.0.109:8080/v1 \
  --model gemma-4-12b-it-UD-Q3_K_XL \
  --model-label gemma4-12b-q3-jetson-toy \
  --limit 2 \
  --out runs/private/toy-gemma
```

Then create a safe public summary:

```bash
python3 scripts/redact_run.py \
  --run runs/private/toy-gemma \
  --out results/toy-gemma-public.json
```

## Real GPQA-Diamond Subset

Gemma first:

```bash
python3 scripts/run_gpqa.py \
  --csv data/private/gpqa_diamond.csv \
  --base-url http://192.168.0.109:8080/v1 \
  --model gemma-4-12b-it-UD-Q3_K_XL \
  --model-label gemma4-12b-q3-jetson \
  --limit 20 \
  --seed 20260605 \
  --out runs/private/gpqa-gemma4-n20
```

InstinctRazor after switching the Jetson server to `jetson-llm`:

```bash
python3 scripts/run_gpqa.py \
  --csv data/private/gpqa_diamond.csv \
  --base-url http://192.168.0.109:8080/v1 \
  --model InstinctRazor-Qwen3.5-122B-A10B-IQ3_XXS.gguf \
  --model-label instinctrazor-122b-iq3xxs-jetson \
  --limit 20 \
  --seed 20260605 \
  --timeout 900 \
  --out runs/private/gpqa-instinctrazor-n20
```

The IP avoids a macOS/Bash `.local` resolver issue seen during Codex runs. If your shell resolves the WendyOS name normally, `http://wendyos-fearless-valley.local:8080/v1` is also fine.

## Suggested X Framing

Careful language matters:

> This is not a new official GPQA score. It is a public edge-inference demo using a GPQA-Diamond subset, with the dataset kept private per GPQA terms. The question is whether the 122B MoE's reported reasoning advantage survives the real bottleneck on an 8GB unified-memory Jetson.

Good comparison dimensions:

- accuracy on the same hidden subset,
- wall-clock time per item,
- generated tokens/sec,
- server reliability,
- whether full `n=198` is feasible on this hardware.
