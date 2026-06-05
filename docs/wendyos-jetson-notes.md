# WendyOS Jetson Edge LLM Notes

Date: 2026-06-05

These notes are from a hands-on attempt to run GPQA-Diamond evaluation against local LLMs on an NVIDIA Jetson Orin Nano Super 8 GB running WendyOS. They are written for WendyOS developers and avoid private dataset content, tokens, or raw model outputs.

## Setup

- Device: NVIDIA Jetson Orin Nano Super 8 GB, WendyOS on NVMe.
- Wendy device name seen locally: `wendyos-fearless-valley.local`.
- LAN IP used when `.local` resolution failed: `192.168.0.109`.
- Model app: `jetson-llm`, serving OpenAI-compatible llama.cpp on port `8080`.
- Large model tested: `General-Instinct/InstinctRazor-Qwen3.5-122B-A10B-GGUF`, `InstinctRazor-Qwen3.5-122B-A10B-IQ3_XXS.gguf`, about 49 GB.
- Smaller comparison model tested: `google/gemma-4-12B-it` via an Unsloth GGUF quant.

## What Worked

- WendyOS could run a local OpenAI-compatible llama.cpp server on the Jetson.
- The 49 GB InstinctRazor GGUF was present and loadable from `/bigmodels`.
- CUDA-enabled llama.cpp was available in the app image and detected the Orin GPU.
- Extra swap was active, which let the large GGUF load even on an 8 GB device.
- After changing the app entrypoint from `CTX_SIZE:-256` to `CTX_SIZE:-512`, official GPQA-Diamond prompts that previously failed could be accepted and evaluated.

## Issues Observed

### `.local` Resolution Failed Intermittently

Several commands against `wendyos-fearless-valley.local` failed with:

```text
name resolver error: produced zero addresses
```

Switching Wendy CLI control commands to `--device 192.168.0.109` worked, but required network permissions in the local sandbox. The model HTTP endpoint at `http://192.168.0.109:8080` was also more reliable than the `.local` name.

Potential product improvement: provide a first-class fallback from discovered hostname to last-known LAN IP, and include the chosen transport address in command output.

### Logs Were Hard To Retrieve

`wendy device logs` or log-like inspection paths were not reliable in this session. The practical workaround was:

```bash
wendy device apps start jetson-llm --device 192.168.0.109
```

in foreground mode, then reading the streamed output. Detached mode often gave less actionable feedback.

Potential product improvement: make `wendy device apps logs <app>` robust, or expose recent stdout/stderr in `wendy device apps list --json`.

### Detached Start Reported Success But App Stopped

For `jetson-llm`, detached start returned:

```text
Application jetson-llm started.
```

but subsequent app listing showed `jetson-llm` as `STOPPED`, and port `8080` was closed. Foreground start succeeded and streamed the useful llama.cpp load logs.

Potential product improvement: after `--detach`, wait briefly for the container process to remain alive or surface the first crash lines immediately.

### Docker Platform Name Needed Translation

The helper app build initially failed:

```text
no match for platform in manifest: not found
```

The Dockerfile used `alpine:3.20`; Wendy invoked Docker with platform `wendyos/arm64`, while public images publish `linux/arm64`. A local Docker wrapper translated `wendyos/arm64` to `linux/arm64`, after which build and deploy worked.

Potential product improvement: Wendy CLI could translate `wendyos/arm64` to `linux/arm64` at Docker build boundaries while preserving WendyOS metadata elsewhere.

### Model Storage Path Was Surprising

The app's persistent `/models` volume was about 24.7 GB, too small for the 49 GB GGUF. The model instead lived at:

```text
/bigmodels/InstinctRazor-Qwen3.5-122B-A10B-IQ3_XXS.gguf
```

with a host-side safety copy at:

```text
/data/instinctrazor-models/InstinctRazor-Qwen3.5-122B-A10B-IQ3_XXS.gguf
```

Potential product improvement: for large-model apps, expose an explicit "large model cache" volume or make the target storage plan visible before download begins.

### Default Context Was Too Small For GPQA

The app entrypoint defaulted to:

```bash
-c "${CTX_SIZE:-256}"
```

The first official GPQA-Diamond prompt needed 279 prompt tokens through the OpenAI chat path, so llama.cpp rejected it at `n_ctx = 256`. After patching to:

```bash
-c "${CTX_SIZE:-512}"
```

the same benchmark prompt was accepted, and llama.cpp reported `new slot, n_ctx = 512`.

One later n20 subset item still failed through the chat path at `n_ctx = 512`:

```text
request (666 tokens) exceeds the available context size (512)
```

Potential product improvement: expose context size as a normal app setting and avoid shipping large LLM server profiles with a default context below common benchmark prompt lengths.

### Host Hook Quoting Was Fragile

A helper app `postStart` hook was used to patch the installed `jetson-llm` entrypoint. Versions that assigned a shell variable like `entry=/path/to/file` and later referenced `$entry` produced confusing or stale reports. A fully literal hook with the entrypoint path repeated directly was more reliable.

Potential product improvement: document the quoting/evaluation model for WendyOS host hooks and provide a safer structured way to patch app settings.

## Performance Notes

With InstinctRazor at `n_ctx = 512` on this 8 GB Jetson:

- prompt ingestion was roughly `0.57-0.64` tokens/sec;
- answer generation for the short letter-only benchmark response was roughly `0.21-0.22` tokens/sec;
- individual GPQA items took several minutes each.

That makes this setup useful as a "can a 122B MoE run at all on a tiny edge device?" demo, but not a fast interactive research assistant without further optimization.
