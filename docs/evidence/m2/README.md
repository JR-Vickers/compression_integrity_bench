# Milestone 2 observed evidence

**Real local loading/generation feasibility on development tasks, 2026-11-12. Not synthetic model responses, an exploratory pilot study, or held-out performance.** No numerical performance scores or compression conclusions are assigned. Both deployments generated Markdown-fenced JSON for all six prompts: 0/6 pass the existing strict bare-JSON parser. All raw responses remain preserved, with parsed probabilities null.

| Deployment | Weight file bytes | Load seconds | Six generations, seconds | Peak MLX allocation, bytes | Peak process RSS, bytes |
| --- | --- | --- | --- | --- | --- |
| BF16 reference | 3,087,467,144 | 0.3164 | 1.0079 | 3,242,028,692 | 3,461,627,904 |
| 4-bit affine, group 64 | 868,629,082 | 0.2462 | 0.5531 | 1,197,387,536 | 1,236,353,024 |

MLX allocator and process RSS measure different things. Files were hashed before loading, warming file caches; timing is a smoke observation, not a benchmark. Conversion took 1.0518 seconds after download and source verification; its process peak RSS was 5,578,964,992 bytes. Both deployment checks used Metal, identical original tokenizer/template, identical input token IDs for all six pairs, and observed BF16 KV caches. All twelve corrected attempts ended at EOS. No generation exceptions or truncations occurred in those corrected runs.

The pinned source is `Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Source weight SHA-256 is `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee`; the local derivative is `5b6abb3e8bbb783216a1a034fe742de5f25a836f3c642910ce327199c51217e7`. The preparation checks the source against the official Hub LFS hash. No calibration corpus is used. The original LICENSE remains in the cached source snapshot; derivative redistribution is outside this task.

## Saved records

- [hardware.json](hardware.json): sanitized hardware/OS/disk/memory observations and initial tooling. No device serials or UUIDs.
- [candidates.json](candidates.json): official model IDs, revisions, ungated availability, licenses, architecture support, source links, and selection rationale. Alternatives were inspected, not run.
- [prepared.json](prepared.json): file-by-file source/derivative hashes, tensor dtype counts, conversion settings/timing, package versions, and source lineage.
- [reference.json](reference.json) and [quantized.json](quantized.json): byte-for-byte copies of the corrected check artifacts, with exact messages, rendered text, token IDs, raw outputs, statuses, cache precision, timings, and memory observations.
- [verification.json](verification.json): saved checks of pairing, failure coverage, unchanged repeated output text, and artifact hashes. Default offline tests independently audit these saved records.
- [failures.json](failures.json): preserved sandbox failure and the initial cache-audit bug, including original artifact hashes and paths. Those initial runs were not overwritten or pooled with the corrected runs.

The versioned [configuration](../../../configs/feasibility-qwen25-1.5b.json) and [dependency pins](../../../requirements-feasibility.txt) define reproduction. The root [README](../../../README.md#local-deployment-feasibility-milestone-2) contains verified commands. The probe stores `invocation.json` before loading; per-request files precede generation, streamed text/token events are flushed to JSONL, and final attempt/check records are separate files. Original artifacts are in `outputs/m2-prepare`, `outputs/m2-reference`, `outputs/m2-quantized`, `outputs/m2-reference-v2`, and `outputs/m2-quantized-v2`, with corresponding `.log` files. They and weights under `.cache/m2-qwen25` are Git-ignored. Absolute paths in snapshots describe the observed machine; new preparation creates local paths for the reproducing machine.

The initial checks and corrected checks total 24 real generations. Corrected raw output text matched the first run for each of the twelve logical prompts. This repetition repaired metadata collection; it is not an independent sample or a selected best attempt. No outputs were changed into bare JSON or reprompted for validity.
