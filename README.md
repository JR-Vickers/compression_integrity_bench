# Compression Integrity Bench

CIB investigates how quantization changes specified epistemic behaviors. The Milestone 1 workflow uses **synthetic development fixtures only**. Milestone 2 adds a separate, explicit local MLX loading/generation check using a real BF16/4-bit pair. Neither workflow establishes compression effects. Research scope and open choices live in [PROJECT.md](docs/PROJECT.md), [METHODOLOGY.md](docs/METHODOLOGY.md), and [PLAN.md](docs/PLAN.md).

## Offline setup and workflow

Run from the repository root with Python 3.11 or newer. Runtime and tests use only the Python standard library; no credentials, accelerator, network, or model downloads are required. The source workflow also works on a Python installation without packaging tools:

```sh
python3 -m venv .venv
export PYTHONPATH="$PWD/src"
mkdir -p outputs/fixture-v1
.venv/bin/python -m cib fixture --output outputs/fixture-v1/raw.json
.venv/bin/python -m cib score --raw outputs/fixture-v1/raw.json --output outputs/fixture-v1/scores.json
.venv/bin/python -m cib report --raw outputs/fixture-v1/raw.json --scores outputs/fixture-v1/scores.json --output outputs/fixture-v1/report.md
.venv/bin/python -m unittest discover -s tests -v
```

Outputs are created exclusively: use a new directory or new filenames when repeating commands. Existing artifacts are never replaced. Open `outputs/fixture-v1/report.md` in a Markdown reader. It contains the full configuration, coverage counts, scenario metrics, independent targets, paired exact inputs, all raw responses, and failures.

To rescore saved records and regenerate the report without producing responses:

```sh
.venv/bin/python -m cib score --raw outputs/fixture-v1/raw.json --output outputs/fixture-v1/rescored.json
.venv/bin/python -m cib report --raw outputs/fixture-v1/raw.json --scores outputs/fixture-v1/rescored.json --output outputs/fixture-v1/regenerated.md
```

The test suite verifies that raw bytes remain unchanged and repeated scoring is byte-identical. Run IDs and timestamps differ across new response-production runs; scripted response content and analysis are deterministic.

For an installed `cib` entry point, the build prerequisite is setuptools >=68 (install it separately if unavailable). With that prerequisite installed, installation itself can be offline:

```sh
.venv/bin/python -m pip install --no-cache-dir --no-index --no-build-isolation --no-deps -e .
.venv/bin/cib --help
```

Observed setup: CPython 3.11.17, pip 26.2, setuptools 84.0.0 on macOS arm64; the default tests also pass on CPython 3.15.0. No runtime or test dependencies were installed. The commands above were exercised; packaging prerequisites can vary by Python distribution.

## What the fixture measures

Two hand-authored base scenarios have priors 0.5 and 0.2, supporting, opposing, and uninformative evidence, and original/swapped labels. The opposing evidence is weaker in the rare-prior scenario. Label variants remain grouped with their base scenario. Both scenarios share a template cluster; these are engineering examples, not a research sample.

Each of the 12 scenario/condition/label combinations has separate self-contained pre and post requests for each scripted provider: 24 requests per provider, 48 total. Post requests restate the prior and evidence and never include a generated pre answer. Providers receive identical rendered inputs. Provider scripts contain hand-entered probabilities independently of the scorer's exact-fraction Bayes calculation.

`fixture-perfect` has all valid, target-correct responses. `fixture-perturbed` contains known wrong probabilities plus one malformed output, one refusal, one truncation, and one infrastructure error. Stop statuses are scripted metadata, not guesses from response prose. There is one attempt per request and no retries or reprompts.

Parsing accepts only a JSON object containing exactly `probability`, whose value must be a finite JSON number in [0,1]. Duplicate keys, booleans, strings, extra fields, out-of-range numbers, and surrounding prose are invalid. JSON whitespace is accepted. This is a development parser choice, not a frozen study protocol.

The scorer calculates posterior absolute error, prior absolute error, update error, and uninformative-evidence drift. Conditions and label variants are equally weighted within each base scenario; scenarios receive equal weight. Each metric requires all its eligible conditions to be scoreable for a scenario mean. A valid incorrect answer gets its actual numerical loss; an invalid observation gets a missing score. Reports show complete-scenario contrasts and conservative full-set posterior-loss bounds using missing losses in [0,1]. These are not confidence intervals. Direction/stability thresholds are explicitly `null` and those diagnostics are disabled.

## Records and limitations

[ARCHITECTURE.md](docs/ARCHITECTURE.md) describes record ownership and lineage; [DECISIONS.md](docs/DECISIONS.md) records development choices. Small versioned task definitions and response scripts live in `src/cib/data/`; bulk outputs, models, caches, and credentials are ignored by Git. Raw v1 records include a complete task snapshot and are supported by this fixture implementation; new fixture/protocol versions require explicit implementation support.

Milestones 1–4 are implemented: offline fixtures, local feasibility, a resumable MLX runner, and a complete bounded exploratory pilot with controls and saved-output analysis. There is no empirical uncertainty analysis, held-out evaluation, or preservation threshold. The pilot found insufficient updating competence relative to the unchanged-prior baseline; next is a fresh exploratory instrument/reference suitability check before a frozen study. The original grant proposal was not present in the initial repository and has not been reconstructed.

## Local deployment feasibility (Milestone 2)

Selected engineering pilot pair: official `Qwen/Qwen2.5-1.5B-Instruct` at revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, **original BF16 reference** versus a **locally derived 4-bit affine/group-64** variant. Both use MLX-LM 0.32.2 / MLX 0.32.4 on the same Apple GPU and the exact original tokenizer/template. This does not select the final study models. See [D004–D005](docs/DECISIONS.md#d004--local-pilot-deployment-pair) for verified alternatives, licensing/provenance, controls, and confounds, and [saved evidence](docs/evidence/m2/README.md) for raw outputs and measurements.

Observed on a 64 GiB M4 Max, macOS 15.7.7: each deployment loaded and generated all six predefined task prompts to EOS. Peak MLX allocations were 3.24 GB (reference) and 1.20 GB (quantized); process peak RSS was 3.46 GB and 1.24 GB. These are decimal GB, distinct counters, and smoke measurements rather than performance benchmarks. All twelve responses were Markdown-fenced JSON: **0/6 per deployment pass the unchanged strict bare-JSON parser**. Probabilities remain missing; no numerical task performance is claimed. No prompts or parser rules were changed to obtain a favorable result.

The following commands were verified from the repository root. They require Apple silicon with Metal access and Python 3.11. Preparation downloads approximately 3.1 GB of public source weights and saves an approximately 0.87 GB derivative. Initial dependency installation/preparation needs network access; generation uses local files with Hub/Transformers offline mode. No credentials or paid services are used. Keep the standard-library fixture environment separate:

```sh
python3.11 -m venv outputs/mlx-env
uv --cache-dir outputs/uv-cache pip install --python outputs/mlx-env/bin/python -r requirements-feasibility.txt
export PYTHONPATH="$PWD/src"
outputs/mlx-env/bin/python -m cib.feasibility prepare --config configs/feasibility-qwen25-1.5b.json --artifacts .cache/m2-qwen25 --output outputs/m2-prepare > outputs/m2-prepare.log 2>&1
outputs/mlx-env/bin/python -m cib.feasibility check --config configs/feasibility-qwen25-1.5b.json --prepared outputs/m2-prepare/prepared.json --deployment reference --output outputs/m2-reference-v2 > outputs/m2-reference-v2.log 2>&1
outputs/mlx-env/bin/python -m cib.feasibility check --config configs/feasibility-qwen25-1.5b.json --prepared outputs/m2-prepare/prepared.json --deployment quantized --output outputs/m2-quantized-v2 > outputs/m2-quantized-v2.log 2>&1
```

Run checks sequentially in separate processes. Output directories and derivative model directories must be new: after an existing run, choose new `--output` paths/log filenames; for a new preparation also choose a new `--artifacts` root. Existing raw records are never replaced. If preparation already exists on this machine, use just the two `check` commands with new output paths. The cached source contains the original license. No upload occurs.

The probe enforces pinned backend versions, verifies downloaded source weights are BF16 and match the official LFS hash, and fingerprints both artifacts before loading. Both deployments intentionally load the source tokenizer rather than the converter's reserialized copy. The same greedy settings, original EOS IDs, 64-token output budget, 2048-token context acceptance limit, and full unquantized KV caches apply to both. No separate reasoning mode, output constraints, penalties, retries, or generated prior answers enter the inputs. Floating-point accumulation remains backend-defined; quantized and BF16 kernels differ.

The first sandbox preparation failed because Metal was unavailable; rerunning with local GPU access succeeded. Initial checks completed generation but failed cache dtype inspection on its integer offset; those records remain at `outputs/m2-reference` and `outputs/m2-quantized`. The fixed `*-v2` records preserve the same prompts and raw text and include BF16 cache evidence. In a restricted execution environment, local Metal access must be permitted to run these commands. Failures and partial streamed outputs remain saved rather than being silently retried.

Default regression checks still need no MLX installation, network, model files, or accelerator:

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

All 13 tests passed on CPython 3.11.17 and 3.15.0. The original offline fixture commands were rerun successfully with artifacts at `outputs/m2-offline-regression/report.md`.

## Integrated local runner and diagnostic rescoring (Milestone 3)

The integrated runner uses the same pinned model artifacts and dependencies above. It always plans the **full 24-request development set per deployment** (two scenarios, three conditions, two labels, two stages), independently of the six M2 probe selections in the model configuration. The commands below ran successfully using the existing preparation. They execute only six new attempts per deployment, sequentially, and retain 18 unexecuted observations each. Metal access is required for generation; no downloads or paid services occur. Choose a new run directory for a new experiment.

```sh
export PYTHONPATH="$PWD/src"
outputs/mlx-env/bin/python -m cib.runner run --run outputs/m3-integration --deployment reference --limit 6
outputs/mlx-env/bin/python -m cib.runner run --run outputs/m3-integration --deployment quantized --limit 6
.venv/bin/python -m cib.runner snapshot --run outputs/m3-integration --output outputs/m3-integration/raw-final.json
.venv/bin/python -m cib score --raw outputs/m3-integration/raw-final.json --output outputs/m3-integration/strict-final.json
.venv/bin/python -m cib score --raw outputs/m3-integration/raw-final.json --parser outer-json-fence-v1 --output outputs/m3-integration/diagnostic-final.json
.venv/bin/python -m cib report --raw outputs/m3-integration/raw-final.json --scores outputs/m3-integration/diagnostic-final.json --output outputs/m3-integration/report-final.md
```

Defaults resolve to `--config configs/feasibility-qwen25-1.5b.json --prepared outputs/m2-prepare/prepared.json`; pass these options to use another preparation of the same pinned protocol. The original per-call probe configuration retains `generation.retries=0`; the runner's separately recorded policy permits **one infrastructure retry on a later invocation**, with both attempts saved. Returned malformed/incorrect answers, refusals and truncations never cause retries. Repeating a positive `--limit` resumes pending observations and advances beyond the completed prefix; it can execute additional prompts. Once the plan is exhausted it executes none. `--limit 0` executes none and was verified for both deployments without MLX access:

```sh
.venv/bin/python -m cib.runner run --run outputs/m3-integration --deployment reference --limit 0
.venv/bin/python -m cib.runner run --run outputs/m3-integration --deployment quantized --limit 0
```

The run directory preserves the original plan, loaded precision metadata, immutable per-attempt starts/results, flushed token streams and exact rendered inputs/token IDs. Interrupted attempts retain partial text and may be retried once. Snapshot, scoring and reporting create new destinations exclusively; use new filenames for every repeat. Journals are the only output cache; artifact, messages, actual rendered/tokenized input, decoding and trial identity separate cache entries. A lock prevents concurrent modification. Scorer-only targets never enter the adapter.

Reuse M2 outputs without inference, with explicit source lineage and no changes to original files:

```sh
mkdir -p outputs/m3-m2-final
.venv/bin/python -m cib.runner import-m2 --config configs/feasibility-qwen25-1.5b.json --prepared outputs/m2-prepare/prepared.json --reference outputs/m2-reference-v2/checked.json --quantized outputs/m2-quantized-v2/checked.json --output outputs/m3-m2-final/raw.json
.venv/bin/python -m cib score --raw outputs/m3-m2-final/raw.json --output outputs/m3-m2-final/strict.json
.venv/bin/python -m cib score --raw outputs/m3-m2-final/raw.json --parser outer-json-fence-v1 --output outputs/m3-m2-final/diagnostic.json
.venv/bin/python -m cib report --raw outputs/m3-m2-final/raw.json --scores outputs/m3-m2-final/strict.json --output outputs/m3-m2-final/strict-report.md
.venv/bin/python -m cib report --raw outputs/m3-m2-final/raw.json --scores outputs/m3-m2-final/diagnostic.json --output outputs/m3-m2-final/report.md
```

`strict-probability-v1` remains the default. Opt-in `outer-json-fence-v1` accepts bare strict JSON or one complete outer triple-backtick block, unlabeled or lowercase `json`, with newlines around its JSON body. It then applies the same strict schema and probability checks. Extra prose/answers, duplicate keys and invalid values remain malformed. This is an **exploratory methodology amendment after seeing development responses**, not a replacement primary scoring policy. Earlier M2 strict scores remain missing. Both real reports show strict and diagnostic coverage separately.

| Saved set | Deployment | Strict compliance / completed | Diagnostic scoreable / completed | Unexecuted / planned |
| --- | --- | --- | --- | --- |
| M2 rescoring | BF16 | 0/6 | 6/6 | 18/24 |
| M2 rescoring | 4-bit | 0/6 | 6/6 | 18/24 |
| New integration | BF16 | 0/6 | 6/6 | 18/24 |
| New integration | 4-bit | 0/6 | 6/6 | 18/24 |

All 12 new attempts ended at EOS with BF16 KV caches and matched rendered inputs/token IDs. The two sets use different six-request subsets and are analyzed separately. No scenario is fully observed; scenario means and full-set point contrasts are withheld. Reports retain independent condition losses and conservative full-set bounds. For example, M2 balanced/support posterior target is 0.8: BF16 reports 0.6 (absolute error 0.20), 4-bit reports 0.64 (0.16); balanced/oppose target is 0.2: BF16 reports 0.3 (0.10), 4-bit reports 0.4 (0.20). These are exploratory examples, not aggregate compression findings.

The token audit verifies that fences originate in generated tokens, not instrumentation. It requires only the optional environment's tokenizer library and the existing source tokenizer/streams; it does not load MLX or generate responses:

```sh
outputs/mlx-env/bin/python scripts/audit_m2_streams.py --output outputs/m3-m2-final/stream-audit.json
```

Offline regression and saved-output regeneration remain independent of Metal/network/models:

```sh
.venv/bin/python -m unittest discover -s tests -v
mkdir -p outputs/m3-offline-regression
.venv/bin/python -m cib fixture --output outputs/m3-offline-regression/raw.json
.venv/bin/python -m cib score --raw outputs/m3-offline-regression/raw.json --output outputs/m3-offline-regression/scores.json
.venv/bin/python -m cib report --raw outputs/m3-offline-regression/raw.json --scores outputs/m3-offline-regression/scores.json --output outputs/m3-offline-regression/report.md
.venv/bin/python -m cib score --raw outputs/m3-m2-final/raw.json --parser outer-json-fence-v1 --output outputs/m3-m2-final/rescored.json
.venv/bin/python -m cib report --raw outputs/m3-m2-final/raw.json --scores outputs/m3-m2-final/rescored.json --output outputs/m3-m2-final/regenerated.md
```

All 19 offline tests passed on CPython 3.11.17. They cover strict/diagnostic boundaries, independent numerical targets, pairing, resume/interruption and retry exhaustion, cache separation, raw immutability, deterministic rescoring and report lineage. [M3 evidence](docs/evidence/m3/README.md) contains the audit findings, hashes and saved integration excerpts. `/.cache/`, model files, environments and generated run outputs remain Git-ignored.

Limitations: one pinned development instrument/pair; sequential deployment order; backend-defined accumulation and different quantized kernels; tiny incomplete engineering samples; no empirical uncertainty intervals or study conclusions. MLX has no refusal flag: textual refusals are malformed unless an upstream explicit refusal status exists. Format reliability, capability controls, final model/sample selection and preservation margins remain unresolved. These were the M3 handoff limitations. The completed Milestone 4 pilot below assesses format and capability controls; its pilot-only primary policy preserves these historical results.


## Exploratory pilot (Milestone 4)

The complete [pilot report](docs/evidence/m4/README.md) records 344/344 planned/executed/completed/primary-scoreable observations: 144 main +16 controls +12 repeats per deployment. All used the existing local pair and frozen `configs/pilot-v1.json` / `src/cib/data/updating-pilot-v1.json`. This explicitly authorized pilot uses **outer-json-fence-v1 as primary**: bare strict probability JSON or one complete outer unlabeled/lowercase-json code fence, with newlines around its body; exactly one finite numeric `probability` in [0,1], no extra prose/fields/answers, duplicate keys, invalid values or repairs. Strict bare-JSON compliance remains separately reported over completed eligible responses: **0/172 for each deployment**. Primary coverage is **172/172 each**, main coverage 144/144. Historical strict defaults and M2/M3 labels are preserved.

On the complete 12-scenario main set, BF16 / 4-bit posterior absolute errors are **0.17446055 / 0.18287535** (72/72 terms each); paired loss change is **+0.00841480**, positive = larger 4-bit loss. Neither beats the unchanged-prior baseline (0.13601504, synthetic 72/72 targets). Both pass 4/4 prior, arithmetic and format-value controls but 0/4 likelihood controls, all primary-scoreable. All 12/12 repeats match exactly. The reference/instrument combination is not ready for a frozen study. This is numerical updating, not empirical uncertainty calibration, preservation evidence or a general quantization claim.

Verified generation commands below used no new model download and require local Metal access. On the completed run they now generate zero attempts; choose a new `--run` directory for a new experiment. Defaults use the original feasibility config and `outputs/m2-prepare/prepared.json`. Fixed single infrastructure retry bounds the full pilot at 688 calls; actual calls were 344.

```sh
export PYTHONPATH="$PWD/src"
outputs/mlx-env/bin/python -m cib.runner run --pilot --run outputs/m4-pilot-v1 --deployment reference --limit 172
outputs/mlx-env/bin/python -m cib.runner run --pilot --run outputs/m4-pilot-v1 --deployment quantized --limit 172
.venv/bin/python -m cib.runner snapshot --run outputs/m4-pilot-v1 --output outputs/m4-pilot-v1/raw.json
.venv/bin/python -m cib.pilot score --raw outputs/m4-pilot-v1/raw.json --output outputs/m4-pilot-v1/scores.json
.venv/bin/python -m cib.pilot report --raw outputs/m4-pilot-v1/raw.json --scores outputs/m4-pilot-v1/scores.json --output outputs/m4-pilot-v1/report.md
```

Snapshot/score/report destinations must be new; these recorded files already exist. Use the dedicated pilot scorer/report to retain its primary policy and allocation summaries. Repeat the following **offline** audit with a new output directory; it never invokes inference:

```sh
PYTHONPATH=src .venv/bin/python scripts/verify_pilot.py --run outputs/m4-pilot-v1 --output outputs/m4-verification-v2
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Observed: 23 offline tests pass; all 1,039 original pilot files were unchanged during rescoring; scores and reports regenerate byte-identically against the same source/score inputs. A report-only source change is retained in source lineage, with numerical equality to original scoring checked separately. Full raw/journal/token streams live in `outputs/m4-pilot-v1/`; the full updated report is `outputs/m4-verification-v2/report.md`. Compact measured summaries, examples and hashes are versioned in `docs/evidence/m4/`. Fixture generation/scoring/reporting was verified again at `outputs/m4-offline-fixture/` with the original strict policy. No earlier evidence was replaced.

## Updating diagnosis (Milestone 4b)

The [M4b evidence report](docs/evidence/m4b/README.md) audits all four original likelihood controls, exact rendered prompts/raw responses, independent targets, largest drift cases and every quantized prior-error case. No target, conditional-direction, pairing or scorer defect was demonstrated; historical M4 results remain unchanged.

The fixed wording diagnostic completed180/180 requests within its200-call ceiling; the separately triggered official Qwen2.5-7B-Instruct **unquantized BF16** check completed60/60 within its100-call ceiling. Primary parser coverage is 240/240; strict compliance 0/240. Mathematical direct-likelihood controls score4/4 for both small deployments, versus original 0/4; clearer wording removes the quantized prior complements. Updating/drift gates still fail for both small deployments and the verified 7B reference. All repeats reproduce exactly. Neither reference replacement nor benchmark expansion is justified yet. Next is one new exploratory check separating Bayes-rule application from numerical expression evaluation on unequal priors and irrelevant evidence.

Verified saved-output commands below require no inference or MLX. Use new output directories when repeating them; recorded destinations already exist:

```sh
export PYTHONPATH="$PWD/src"
.venv/bin/python scripts/audit_m4b.py --output outputs/m4b-audit-reproduction-v1
.venv/bin/python scripts/verify_diagnostic.py --run outputs/m4b-wording-v1 --output outputs/m4b-wording-verification-v1 --historical-hashes outputs/m4b-audit-v1/original-hashes.json
.venv/bin/python scripts/verify_diagnostic.py --run outputs/m4b-reference-7b-v1 --output outputs/m4b-reference-verification-v1 --historical-hashes outputs/m4b-audit-v1/original-hashes.json
.venv/bin/python -m unittest discover -s tests -v
```

All 29 offline tests pass. Regeneration confirms unchanged historical/new raw records and byte-identical repeated scores/reports. The [report](docs/evidence/m4b/README.md#verification-cost-and-reproduction) gives the full generation, preparation, snapshot and scoring commands, pinned provenance and artifact paths. The runner's explicit `--diagnostic` selects this instrument; `python -m cib.diagnostic score/report` analyze it. Larger-model preparation verifies official shard hashes and BF16 headers and performs no quantization. Optional model files and environments remain Git-ignored. Fixture commands were reverified at `outputs/m4b-offline-fixture/`. Findings remain exploratory, without empirical-calibration or preservation claims.
