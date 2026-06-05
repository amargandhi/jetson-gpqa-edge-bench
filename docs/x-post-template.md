# X Post Template

Draft:

```text
I ran a small, source-respecting GPQA-Diamond edge demo on an 8GB Jetson Orin Nano running WendyOS.

Models:
- Gemma 4 12B Q3 GGUF
- InstinctRazor Qwen3.5 122B-A10B IQ3_XXS GGUF

This is not a new official GPQA score. The GPQA data stays private per dataset terms. The public result is aggregate only.

Question:
Does the slow 122B MoE preserve enough reasoning advantage on an 8GB unified-memory edge box to justify waiting?

Same hidden n20 subset, seed 20260605:
- Gemma 4 12B: 7/20, 35.0%, 0 failures, 2.64 sec/item
- InstinctRazor 122B MoE: 8/20, 40.0%, 1 context failure, 392.8 sec/item

Useful finding:
The 122B MoE did run on the tiny Jetson and got one more item right on this small subset, but the real story was the bottleneck: about 110 minutes for n20, roughly 0.58 prompt tok/s and 0.21 generated tok/s.

So the value here is not "new leaderboard score." It is a practical edge finding: context length and prompt ingestion dominate GPQA-style reasoning on this 8GB setup.

Repo:
https://github.com/amargandhi/jetson-gpqa-edge-bench
```

Short thread shape:

1. State the hardware and models.
2. State why this is a demo, not a leaderboard claim.
3. Show same-subset accuracy and latency.
4. Call out the memory bottleneck honestly.
5. Tag/credit GPQA, Qwen, Google Gemma, Unsloth, and General Instinct sources.
