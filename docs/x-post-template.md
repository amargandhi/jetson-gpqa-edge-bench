# X Post Template

Draft:

```text
I ran a small, source-respecting GPQA-Diamond edge demo on an 8GB Jetson Orin Nano.

Models:
- Gemma 4 12B Q3 GGUF
- InstinctRazor Qwen3.5 122B-A10B GGUF

This is not a new official GPQA score. The GPQA data stays private per dataset terms. The public result is aggregate only.

Question:
Does the slow 122B MoE preserve enough reasoning advantage on an 8GB unified-memory edge box to justify waiting?

Results:
[fill in n, accuracy, avg seconds/item, tok/s, failures]

Useful finding:
[fill in: accuracy gap, latency wall, or system bottleneck]
```

Short thread shape:

1. State the hardware and models.
2. State why this is a demo, not a leaderboard claim.
3. Show same-subset accuracy and latency.
4. Call out the memory bottleneck honestly.
5. Tag/credit GPQA, Qwen, Google Gemma, Unsloth, and General Instinct sources.
