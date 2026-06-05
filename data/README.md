# Private Data

Do not commit GPQA examples, answers, or answer keys.

The official GPQA dataset is gated and asks users not to reveal examples online.

After accepting access on Hugging Face, place the official Diamond CSV here:

```text
data/private/gpqa_diamond.csv
```

Download helper:

```bash
export HUGGINGFACE_TOKEN=hf_...
python3 scripts/download_gpqa.py
```

This directory is intentionally kept public-data-free.
