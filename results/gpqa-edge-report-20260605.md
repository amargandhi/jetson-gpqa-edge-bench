# GPQA-Diamond Edge Demo: Jetson Orin Nano 8 GB

Date: 2026-06-05

This is a source-respecting edge-inference demo, not an official GPQA score or leaderboard submission. The GPQA-Diamond CSV, answer keys, prompts, and raw completions remain private. Public files in this repo contain only aggregate results.

## Hardware And Runtime

- Device: NVIDIA Jetson Orin Nano Super 8 GB running WendyOS.
- API path: local OpenAI-compatible llama.cpp server on the Jetson.
- Dataset: official GPQA-Diamond CSV, deterministic shuffled subset, `n=20`, seed `20260605`.
- Prompt: deterministic A/B/C/D shuffle, one-letter answer requested.
- Private data path: `data/private/gpqa_diamond.csv`.
- Private run paths: `runs/private/`.

## Results

| Model | Quant / server label | Correct | Accuracy | Failures | Avg sec/item | Wall time | Avg prompt tok/s | Avg generated tok/s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemma 4 12B IT | `gemma4-12b-q3-jetson` | 7/20 | 35.0% | 0 | 2.644 | 52.884 s | 99.53 | 10.6824 |
| InstinctRazor Qwen3.5 122B-A10B | `instinctrazor-122b-iq3xxs-jetson-ctx512` | 8/20 | 40.0% | 1 | 392.799 | 6605.726 s | 0.58 | 0.2144 |

InstinctRazor successful-request average latency was `413.365 s` because the one failed request returned quickly. Its full run took about `110.1 minutes`.

## What Happened

InstinctRazor initially served with `n_ctx = 256`. That was too small for the first official GPQA-Diamond prompt through this chat path; the server rejected a `279` token request. After patching the WendyOS app entrypoint to `n_ctx = 512`, the model accepted most prompts and completed the n20 run.

One prompt still failed at `n_ctx = 512`:

```text
request (666 tokens) exceeds the available context size (512)
```

So the published InstinctRazor aggregate includes one API failure. This is intentional and useful to report, because it shows that a 512-token context is still not enough for all GPQA-Diamond prompts under this server/chat-template configuration.

## Bottleneck

The practical bottleneck was not answer generation length. The benchmark asked for only one letter, and successful InstinctRazor completions were usually two generated tokens. The bottleneck was prompt ingestion for a 49 GB MoE GGUF on an 8 GB unified-memory Jetson.

Observed successful-request aggregate:

| Model | Successful prompt tokens, min / median / max | Successful latency, min / median / max |
| --- | ---: | ---: |
| Gemma 4 12B IT | 169 / 253.5 / 603 | 1.482 s / 2.654 s / 5.448 s |
| InstinctRazor 122B MoE | 168 / 253 / 460 | 252.631 s / 392.365 s / 754.957 s |

On this run, InstinctRazor was about `148.6x` slower by average seconds per item and about `49.8x` slower by generated tokens/sec. The average prompt ingestion rate was about `172.9x` slower.

## Interpretation

The small subset showed InstinctRazor ahead by one question: `8/20` versus Gemma's `7/20`. At `n=20`, that is only a five percentage point swing and should not be over-interpreted. The more defensible finding is operational:

> On this 8 GB Jetson/WendyOS setup, InstinctRazor can run and can answer GPQA-Diamond prompts after a context-size fix, but context length and prompt-ingest speed dominate the user experience.

For an X post, the useful point is not "the 122B model wins" or "Gemma wins." It is:

> A 122B MoE can be squeezed onto a tiny Jetson, but for GPQA-style reasoning the edge bottleneck is context and prompt processing. On the same hidden n20 subset, it bought only one extra correct answer while taking about 110 minutes.

## Sources

- GPQA dataset: https://huggingface.co/datasets/Idavidrein/gpqa
- GPQA paper: https://arxiv.org/abs/2311.12022
- Qwen3.5-122B-A10B model card: https://huggingface.co/Qwen/Qwen3.5-122B-A10B
- General Instinct blog post: https://general-instinct.com/blog/frontier-moe-sub-4-bit
- InstinctRazor GGUF: https://huggingface.co/General-Instinct/InstinctRazor-Qwen3.5-122B-A10B-GGUF
- Gemma 4 12B IT: https://huggingface.co/google/gemma-4-12B-it
- Unsloth Gemma 4 12B GGUF: https://huggingface.co/unsloth/gemma-4-12b-it-GGUF

