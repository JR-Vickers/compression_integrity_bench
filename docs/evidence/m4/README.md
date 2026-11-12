# Milestone 4: bounded exploratory pilot v1

All Milestone 4 acceptance criteria are met for instrument assessment and workflow execution, 2026-11-12. **The current reference/instrument combination is not validated for a frozen study.** No preservation or general quantization conclusion is supported.

The pair remains provisional: Qwen/Qwen2.5-1.5B-Instruct at `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, original BF16 versus directly derived MLX 4-bit affine/group-64, on the same 64 GiB M4 Max. D004 controls and deployment confounds apply.

## Fixed protocol and parsing

The [configuration](../../../configs/pilot-v1.json), [dataset](../../../src/cib/data/updating-pilot-v1.json), D008 and Methodology §17 were written before any pilot generation. The run plan was initialized with `--limit 0` before GPU execution. The manifest embeds the exact dataset and allocation. Twelve base scenarios use three wording templates (urn/factory/packet), with four shared numerical patterns, priors 0.1/0.25/0.5/0.75, varied likelihood ratios, supporting/opposing/uninformative branches, complementary label variants and self-contained pre/post requests. They form 144 main requests per deployment. Sixteen controls and twelve fixed repeats give **172 per deployment, 344 total**. The repeated numerical patterns restrict template generalization; these are exploratory, not held-out observations.

Pilot primary numerical parser: **outer-json-fence-v1**, reusing the unchanged M3 implementation. It accepts bare valid JSON or exactly one complete outer triple-backtick fence, unlabeled or labeled lowercase `json`, with newlines separating its body from both fences and optional whitespace outside. The JSON must contain exactly `probability`, with a finite JSON number in [0,1]. Prose, multiple answers/fences, nested fences, duplicate keys, extra fields, booleans, strings, null and invalid values are rejected. No repair, coercion or number extraction occurs. Strict bare-JSON compliance is reported independently over all completed eligible responses. Historical M2/M3 raw records, scores and primary labels remain unchanged. The parser implementation hash is retained in scores and [verification](verification.json).

Both deployments retain matched original tokenizer/template, greedy temperature 0, seed 0, 64 output tokens, 2048 context acceptance, prefill 512, source EOS IDs and BF16 KV, without constraints or generated prior context. Reference ran first, then quantized in separate local processes. At most one infrastructure retry was permitted; maximum possible calls 688, below 800. Limits: 7200 seconds, 12 decimal GB MLX peak, 1 decimal GB run files, checked between calls. No downloads, paid compute or external services were used. The sandbox Metal setup failure was preserved before any generation attempt; permitted GPU execution then succeeded.

## Coverage and numerical results

| Allocation, per deployment | Planned | Executed | Completed at EOS | Primary scoreable | Strict compliant / completed eligible |
| --- | ---: | ---: | ---: | ---: | ---: |
| Main | 144 | 144 | 144 | 144/144 | 0/144 |
| Controls | 16 | 16 | 16 | 16/16 | 0/16 |
| Repeats | 12 | 12 | 12 | 12/12 | 0/12 |
| Total | 172 | 172 | 172 | 172/172 | 0/172 |

All 344 observations have one immutable completed attempt. No generation failure, refusal, truncation, parser failure under the primary policy, retry or unexecuted work occurred. Every response is fenced JSON. Main numerical coverage is 144/144 per deployment, 72/72 pre/post terms (24/24 irrelevant terms), and 12/12 complete scenarios. Main metrics exclude controls and repeats. Equal branches/labels within scenario, then equal scenarios; all estimates therefore use the full declared set. Missing-loss bounds collapse to the observed paired posterior contrast. No empirical uncertainty intervals are claimed.

| Loss (lower is better) | BF16 | 4-bit | 4-bit minus BF16 |
| --- | ---: | ---: | ---: |
| posterior_error | 0.17446055 | 0.18287535 | +0.00841480 |
| prior_error | 0.00000000 | 0.06666667 | +0.06666667 |
| update_error | 0.17446055 | 0.20258198 | +0.02812143 |
| uninformative_drift | 0.17638889 | 0.20277778 | +0.02638889 |

Positive change means larger loss. Both improvement and regression occur within this average. These are descriptive deployment contrasts for this fixed pilot, not population effects.

Condition-level posterior losses (all 24/24 scoreable per condition and deployment; full main parser coverage 144/144):

| Condition | BF16 | 4-bit | Paired change |
| --- | ---: | ---: | ---: |
| support | 0.18309295 | 0.17050749 | -0.01258546 |
| oppose | 0.16389981 | 0.19200745 | +0.02810764 |
| irrelevant | 0.17638889 | 0.18611111 | +0.00972222 |

Per-scenario posterior losses (six/six post terms per scenario/deployment, primary main coverage 144/144):

| Scenario / template | BF16 | 4-bit | Paired change |
| --- | ---: | ---: | ---: |
| t1-s1 | 0.23099099 | 0.24842689 | +0.01743590 |
| t1-s2 | 0.13939394 | 0.16494949 | +0.02555556 |
| t1-s3 | 0.17500000 | 0.20000000 | +0.02500000 |
| t1-s4 | 0.13472222 | 0.16604167 | +0.03131944 |
| t2-s1 | 0.21842689 | 0.26176022 | +0.04333333 |
| t2-s2 | 0.16717172 | 0.17828283 | +0.01111111 |
| t2-s3 | 0.16666667 | 0.08166667 | -0.08500000 |
| t2-s4 | 0.10138889 | 0.13333333 | +0.03194444 |
| t3-s1 | 0.27176022 | 0.28176022 | +0.01000000 |
| t3-s2 | 0.20050505 | 0.18106066 | -0.01944439 |
| t3-s3 | 0.18333333 | 0.09722222 | -0.08611111 |
| t3-s4 | 0.10416667 | 0.20000000 | +0.09583333 |

All four per-scenario metrics, complete condition targets/losses, template summaries, controls, repeats, exact inputs and every attempt appear in the [full regenerated report](../../../outputs/m4-verification-v2/report.md). [summary.json](summary.json) retains compact measured summaries and complete scenario metrics; bulk raw/journal/streams remain Git-ignored.

## Instrument quality and capability controls

Both deployments answer **4/4 prior-reading, 4/4 arithmetic and 4/4 format-control values correctly, but 0/4 likelihood-reading controls**. All four controls in each category are primary-scoreable; strict format compliance remains 0/16 over completed controls. Format-value success does not establish literal instruction compliance. A likelihood control explicitly asks for P(signal|H), with the value stated in the prompt and a warning not to report P(H|signal); both deployments return another value. For example, target 0.1 produces 0.16666666666666666 (BF16) and 0.166667 (4-bit). The failure may reflect conditional-probability interpretation or instruction following; these four controls cannot distinguish the mechanisms. They expose a prerequisite competence problem even though simple arithmetic and reading succeed.

The synthetic unchanged-prior baseline has posterior/update loss **0.13601504** and zero prior loss/drift; constant 0.5 has posterior loss **0.27084410**; the analytic oracle has zero losses. All baseline targets are defined for 72/72 pairs (24/24 drift); these are hypothetical calculations, not model observations. **Neither model beats the unchanged-prior baseline on the full instrument.** The reference therefore does not demonstrate sufficient updating competence to freeze this combination for a study. BF16 reads all main priors correctly; 4-bit complements the prior in t3-s1 (packet, both labels, all three pre requests), accounting for its main prior loss. Good standalone controls do not guarantee contextual competence.

There is useful diagnostic variation rather than an aggregate numerical ceiling: exact posteriors occur in 5/72 BF16 and 4/72 4-bit responses; scenario posterior losses range 0.10139–0.27176 and 0.08167–0.28176 respectively (all 72/72 post terms scoreable per deployment). Individual losses range 0–0.5 and 0–0.45. The likelihood controls show a floor, while simpler controls show ceilings. Equal-likelihood evidence causes substantial drift (24/24 pairs per deployment), making a trivial unchanged-prior response better overall. Baselines distinguish useful updating from activity alone; nonzero changes are not automatically successful updates.

Mean complement inconsistency |q_original+q_swapped−1| is **0.17384259 BF16** and **0.12711806 4-bit**, each 36/36 scoreable label pairs, full main parser coverage 144/144. This swap complements H and changes prior/likelihoods, so the statistic combines numerical and label sensitivity and is not a pure lexical-label effect. Templates reuse the same numerical patterns; only three wording clusters exist. These observations cannot justify an independent-scenario population interval.

All twelve repeated outputs per deployment match the original text and stop status exactly (12/12 primary-scoreable pairs; maximum probability difference zero). Greedy repeats assess this local backend's repeatability, not stochastic variance or additional scenarios.

## Representative examples

Examples are diagnostic, not the analysis subset. All are primary-scoreable and strict-format failures (their raw form is ` ```json `, newline, JSON object, newline, closing triple backticks). [examples.json](examples.json) includes the exact model-visible prompts, rendered inputs, token IDs, raw outputs, request/cache IDs and source lineage.

| Case | Analytic target | BF16 response | 4-bit response | Interpretation |
| --- | ---: | ---: | ---: | --- |
| t1-s3 support swapped | 0.1 | 0.1 | 0.25 | Exact BF16 answer; larger 4-bit loss |
| t2-s3 support original | 0.9 | 0.6 | 0.9 | Exact 4-bit answer |
| t1-s1 irrelevant swapped | 0.9 | 0.4 | 0.6 | Large shared error despite uninformative evidence |
| t3-s3 support original | 0.9 | 0.45 | 0.9 | Largest paired improvement: posterior-loss change −0.45 |
| t3-s4 oppose original | 0.5 | 0.5 | 0.8333333333333334 | Largest paired regression: +0.33333333 |
| t3-s1 pre original | 0.1 | 0.1 | 0.9 | Context-specific 4-bit prior error |

Every displayed response is primary-scoreable (2/2 where paired); targets are independent of both models. There are no primary-format failures to exemplify. The fenced responses themselves demonstrate the universal strict-format failure; inventing a malformed pilot output would misrepresent this run.

## Practical cost and verification

BF16: 172 generation calls, **28.67 seconds** summed generation/stream-writing time, **3.242 GB** MLX peak and **3.427 GB** process peak RSS. 4-bit: 172 calls, **15.22 seconds**, **1.195 GB** MLX peak and **1.226 GB** RSS. Decimal GB, different counters. Attempt-start-to-last-completion spans are approximately 29.39 and 16.42 seconds, excluding setup/hashing/loading. Run files occupied about 14.9 MB before verification. These are local operational observations with warmed files, reference-first ordering and normal machine activity, not benchmark throughput claims. Quantized and dense kernels and backend-defined accumulation remain confounds. All 344 attempts audit BF16 KV. A saved-stream audit also confirms that concatenated generated text equals every raw response and each terminal stream event is `stop` (2,902 BF16 and 2,939 4-bit token-bearing stream events).

The offline regeneration audit checked **1,039 original files**, including the plan, all starts/results/streams, loaded metadata, the setup failure and original raw/scores/report. Their hashes were unchanged. Repeated scoring produces identical bytes; repeated reports against the same saved score file produce identical bytes; regenerated numerical results equal the original scores. Report-only code additions changed the aggregate source fingerprint, which is retained rather than erased. No inference was repeated for scoring. Both exhausted-plan runner commands returned 0 new attempts using the standard-library environment. All **23 offline tests** pass, and the original fixture workflow succeeds at `outputs/m4-offline-fixture/`. Earlier M2/M3 evidence is unchanged. Exact hashes and checks are in [verification.json](verification.json).

## Artifacts and reproduction

Run from the repository root, with `export PYTHONPATH="$PWD/src"`. Existing files are never overwritten; select new destinations for another audit or experiment. These commands were exercised:

```sh
# Observed generation commands, existing pinned artifacts, local Metal access required.
# Both now return 0 because the full plan is exhausted; use a new --run for new inference.
outputs/mlx-env/bin/python -m cib.runner run --pilot --run outputs/m4-pilot-v1 --deployment reference --limit 172
outputs/mlx-env/bin/python -m cib.runner run --pilot --run outputs/m4-pilot-v1 --deployment quantized --limit 172
.venv/bin/python -m cib.runner snapshot --run outputs/m4-pilot-v1 --output outputs/m4-pilot-v1/raw.json
.venv/bin/python -m cib.pilot score --raw outputs/m4-pilot-v1/raw.json --output outputs/m4-pilot-v1/scores.json
.venv/bin/python -m cib.pilot report --raw outputs/m4-pilot-v1/raw.json --scores outputs/m4-pilot-v1/scores.json --output outputs/m4-pilot-v1/report.md
# Independent regeneration from saved raw records, no model/inference/network.
PYTHONPATH=src .venv/bin/python scripts/verify_pilot.py --run outputs/m4-pilot-v1 --output outputs/m4-verification-v2
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Primary full outputs: `outputs/m4-pilot-v1/{run.json,raw.json,scores.json,report.md}`, immutable `*.start.json`, `*.result.json`, `*.stream.jsonl`, loaded metadata and sandbox setup error. Regenerated outputs: `outputs/m4-verification-v2/{scores.json,rescored.json,report.md,regenerated.md,verification.json}`. Scoring and reporting use the dedicated pilot commands, preserving the historical generic strict default. The report from the verification directory adds the explicit competence assessment and records current source lineage; earlier outputs remain untouched.

Next concrete dependency: a new exploratory instrument version that investigates likelihood-reading failures and irrelevant drift, with fresh tasks and an explicit choice of reference suitability. The existing pair is not silently replaced. Resolve that validity issue before freezing a held-out updating protocol. Milestone 5 also requires separate designs/pilots for the other four dimensions and the dedicated human-review workflow; this pilot does not complete them. Final model selection, held-out sample size, uncertainty method and preservation margins remain unresolved.
