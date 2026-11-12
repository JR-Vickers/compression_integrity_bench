# Milestone 3 observed evidence

Real local engineering checks and exploratory rescoring of development responses, 2026-11-12. No held-out evaluation or preservation finding. The engineering model pair remains Qwen2.5-1.5B-Instruct at `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, original BF16 versus locally derived MLX 4-bit affine/group-64. No model artifacts were downloaded again.

## Inference-path audit

Inspected `src/cib/feasibility.py`, pinned local `mlx_lm/generate.py` (`stream_generate`, around lines 700–770), source tokenizer/template/generation config, prepared artifact inventories, `loaded.json`, all twelve M2 final attempts and their token streams.

- The source template inserts its default Qwen helpful-assistant system message, user text and assistant generation prefix. Both deployments use that same original source tokenizer, template, messages, rendered text and token IDs. The prefix contains no JSON response or Markdown fence. There is no generated pre answer in any post input.
- Controls: temperature 0/greedy, seed 0, 64 new tokens, 2048 input-plus-output acceptance limit, prefill 512; EOS IDs `[151643,151645]`; no extra stop strings, output constraints, penalties, conversation history, separate reasoning mode, or KV quantization. These settings are preserved in the integrated adapter. Sampling defaults cannot affect a temperature-zero argmax.
- MLX-LM emits incremental detokenizer text segments. EOS is removed from displayed text and yields `finish_reason="stop"`; budget exhaustion yields `"length"`. The probe concatenates `response.text` without wrapping it. The new adapter performs the same extraction, saves individual token/text events and maps unknown/missing terminal reasons to infrastructure failure. A length stop remains truncation even if its prefix could parse.
- **All twelve saved M2 generated-token sequences decode exactly to the fenced raw response.** Joining text events gives the same result; no rendered input contains a fence. The first emitted sequence includes token 73594 (triple backticks), 2236 (`json`), 198 (newline). The wrapper therefore originates in model generation, not report formatting or response extraction. The optional [audit script](../../../scripts/audit_m2_streams.py) reproduces this using the existing source tokenizer without MLX/generation.
- Actual loaded reference parameters: 338 BF16 tensors. Quantized: 197 packed uint32 and 535 BF16 tensors, 197 quantized modules. Source/derivative saved inventories match these precisions. Norms/biases and quantization scales remain floating point. Every M2 and new integration KV audit reports BF16. Nominal four-bit weights do not imply all tensors, activations, or arithmetic use four bits; kernel accumulations remain backend-defined. No claim of an entirely BF16 arithmetic graph.

See [stream-audit.json](stream-audit.json) for all decoded strings, matching flags and per-stream hashes; [M2 evidence](../m2/README.md) retains source hashes and original controls.

## Observed coverage and descriptive scores

| Set | Deployment | Completed at EOS | Strict format | Diagnostic scoreable | Unexecuted / full plan |
| --- | --- | --- | --- | --- | --- |
| M2 saved outputs | BF16 | 6 | 0/6 | 6/6 | 18/24 |
| M2 saved outputs | 4-bit | 6 | 0/6 | 6/6 | 18/24 |
| New runner | BF16 | 6 | 0/6 | 6/6 | 18/24 |
| New runner | 4-bit | 6 | 0/6 | 6/6 | 18/24 |

`strict-probability-v1` remains primary; `outer-json-fence-v1` / `updating-diagnostic-v1` is an opt-in exploratory methodology amendment (D006). Strict numerical scores remain missing. All diagnostic values below are independent posterior absolute errors; smaller is better.

| Original-label post case in M2 | Analytic target | BF16 response / loss | 4-bit response / loss |
| --- | --- | --- | --- |
| balanced, support | 0.8 | 0.6 / 0.20 | 0.64 / 0.16 |
| balanced, oppose | 0.2 | 0.3 / 0.10 | 0.4 / 0.20 |
| balanced, irrelevant | 0.5 | 0.6 / 0.10 | 0.6 / 0.10 |
| rare, support | 0.5 | 0.4 / 0.10 | 0.4 / 0.10 |

The two M2 pre responses match their priors (0.5 and 0.2). Missing branch-specific pre answers are not substituted with another branch's response; update/drift scores stay missing where the corresponding pre is absent. Both label variants and all branches remain planned. Neither scenario is complete, so scenario means and full-set point contrasts are withheld. Diagnostic full-set posterior-loss contrast bounds (4-bit minus BF16) are `[-0.66166667, 0.67166667]` for M2 rescoring and `[-0.745, 0.755]` for the new runner; primary strict bounds are `[-1,1]`. These bounds concern missing outcomes, not sampling uncertainty.

The new bounded run executes the first six full-plan requests: balanced/original support, oppose and irrelevant, each with its own pre/post. M2's original selection instead includes two rare-prior requests. They are analyzed separately, never pooled. All new rendered/tokenized pairs match. The new balanced post outputs reproduce the M2 texts, including both a smaller and a larger diagnostic loss in the quantized deployment. This is not an independent sample of models/scenarios or a repeatability study.

## Artifacts and verification

- [integration.json](integration.json): exact request/attempt excerpts for all twelve new generations, source result-file hashes, and per-deployment loaded metadata. Repeated loaded metadata is stored once in this excerpt; full originals remain in the run directory. These are real outputs, explicitly distinct from synthetic test doubles.
- [verification.json](verification.json): raw/derived artifact hashes, observed coverage, diagnostic comparisons/losses, unchanged-raw evidence and byte-identical rescoring. Original `*-v2/checked.json` hashes still match the versioned M2 evidence.
- `outputs/m3-m2-final/raw.json`, `strict.json`, `diagnostic.json`, `strict-report.md`, `report.md`, `rescored.json`, `regenerated.md`: checked legacy import, both scoring policies, reports and regeneration.
- `outputs/m3-integration/`: original journal/streams and loaded metadata; `raw-final.json`, `strict-final.json`, `diagnostic-final.json`, `report-final.md`, `rescored-final.json`, `regenerated-final.md`. Earlier development exports in this directory were preserved.
- `outputs/m3-offline-regression/raw.json`, `scores.json`, `report.md`: successfully executed offline fixture workflow.

The root [README](../../../README.md#integrated-local-runner-and-diagnostic-rescoring-milestone-3) gives exact commands for generation, import, strict/diagnostic scoring, audit and regeneration. Outputs are exclusive: choose new filenames/directories to reproduce. Reusing the integration directory with a positive limit advances to pending requests; `--limit 0` generates none. Both zero-budget invocations were observed to return 0 without MLX loading. Backend doubles separately verify that an exhausted full plan skips every completed observation, interrupted streams retain partial output, retries stop after two infrastructure attempts, and malformed/incorrect/truncated responses receive no extra attempt.

**19 offline tests passed** on CPython 3.11.17, including the saved real integration audit, parser boundaries, pairing, cache separation, recovery/attempt history, raw preservation and deterministic rescoring. `git diff --check` passed. Caches and outputs, including `/.cache/`, remain ignored. The initial sandbox integration invocation could not access Metal and failed before any inference attempt; the bounded reference and quantized runs then succeeded with permitted local GPU access. No inference was rerun merely to rescore or regenerate reports.

Limits: one checkpoint, one template cluster, incomplete development observations, reference-first sequential order, warmed caches, quantized versus dense kernels, no empirical confidence intervals. No native refusal signal exists in MLX: textual refusals are malformed under the numerical schema rather than guessed into a refusal category. Process-interruption recovery is tested; disk/power-loss durability is not guaranteed. Next dependency is an explicitly designed Milestone 4 pilot with instrument/format and capability-control validation; final study choices remain open.
