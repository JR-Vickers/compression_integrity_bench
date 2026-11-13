# Compression Integrity Bench: Development Plan

Status: Working implementation plan, v0.13; bounded source-fidelity pilot executed, human validation and broader M5 packages pending
Updated: 2026-11-12  
Project: Compression Integrity Bench (CIB)  
Repository filename: `PLAN.md`

This is the development roadmap for evaluating how quantization changes the epistemic behavior of open-weight language models. It covers uncertainty calibration, resistance to sustained sycophancy, evidence-sensitive updating, source fidelity, and counterargument representation. The intended research outputs are the benchmark and evaluation harness, a static side-by-side comparison viewer, and a formal writeup.

## 1. Starting position

The project owner has reviewed [PROJECT.md](PROJECT.md) and [METHODOLOGY.md](METHODOLOGY.md) and is satisfied with them as working specifications. Their explicitly proposed scientific choices remain provisional.

The initial repository contained specifications and no implementation. Milestone 1 has a verified offline fixture pipeline. Milestone 2 has observed local BF16/4-bit loading and generation checks, with strict-format failures retained; evidence is recorded in Section 12. These are development feasibility runs, not benchmark findings. Milestone 3 now integrates resumable MLX inference and explicit diagnostic rescoring; Milestone 4 now completes a bounded exploratory pilot; Milestones 5–8 remain pending.

Keep AGENTS.md in the repository root and PROJECT.md, METHODOLOGY.md, and PLAN.md in `docs/`, matching the existing layout and links. Retain the original grant proposal unchanged as `docs/original-proposal.md` when supplied; it was absent at bootstrap. Root README.md describes the verified setup and workflow. Scientific requirements live in METHODOLOGY.md; this plan sequences their implementation and does not override them.

The offline example now constructs tasks, obtains clearly synthetic responses, retains records, calculates scores, compares outputs, and regenerates a report. A separate real feasibility probe now loads a selected local deployment pair. The resumable real comparison runner is now verified. The exploratory pilot is now complete, including explicit primary parsing, controls and repeatability. The M4b/M4c validity checks now also completed; their competence failures park the numerical endpoint and require an explicit replacement/redesign instrument decision before a frozen study.

## 2. Milestone sequence

| Milestone | Outcome | Main dependency | Status |
| --- | --- | --- | --- |
| 1. Offline pipeline | An auditable example runs without model access | Current specifications | Complete — verified 2026-11-12 |
| 2. Deployment feasibility | One reference/quantized pair is chosen and can run | Declared hardware and resource budget | Complete — loading/generation verified 2026-11-12; strict-format failure recorded |
| 3. Real comparison runner | Matched model runs can be resumed, rescored, and compared | Milestones 1 and 2 | Complete — verified 2026-11-12 |
| 4. Exploratory pilot | The instrument and practical workflow are assessed | Real runner and explicit pilot configuration | Complete — 344/344 planned observations, verified 2026-11-12; competence limitation retained |
| 4b. Updating diagnosis | Audit instrument/competence failures and narrow a remedy | Saved pilot plus bounded wording/reference checks | Complete — audit, 180/180 wording and 60/60 larger-reference calls, verified 2026-11-12 |
| 4c. Conditional/rule/numerical diagnosis | Distinguish elicitation and scaffolding from numerical evaluation | Existing 7B BF16 artifacts and fixed fresh diagnostic | Complete — 42/42 calls and immutable regeneration; all forms fail, family parked, 2026-11-12 |
| 5. Full benchmark preparation | All five modules and the dedicated human-review workflow are piloted | Validated pipeline and explicit module designs | In progress — v1/v2 bounded sycophancy pilots complete; validation and other packages pending |
| 6. Study protocol | The full study design is frozen with fresh held-out sets | Pilot findings, feasible matrix, budget, and research decisions | Pending |
| 7. Full empirical study | Planned comparisons and MoE work are accounted for | Frozen protocols, compute, and raters | Pending |
| 8. Viewer, writeup, and release | The three promised outputs and replication instructions are ready | Complete study artifacts and analysis | Pending |

Complete each milestone's relevant checks and routine fixes. Independent preparation may proceed while another dependency is unresolved, but dependencies must remain visible. A working milestone is not evidence that the next milestone is complete. The first functioning pipeline and pilot do not fulfill the full study's five-category scope.

## 3. Milestone 1: Offline pipeline

### Deliverable

A small Python package with a documented command-line workflow. It should exercise the complete path using development fixtures and a deterministic scripted response provider.

### Work

1. Bootstrap `pyproject.toml`, a `src/cib/` package, a focused test suite, a suitable `.gitignore`, and a root `README.md` with actual setup commands. Exclude weights, caches, credentials, and bulk run outputs while keeping small fixtures and configurations versioned.
2. Define minimal versioned records for scenarios, conditions, requests, deployment identity, attempts, raw responses, scores, and run manifests. Preserve scenario grouping and distinguish model-visible inputs from scorer metadata.
3. Add a small hand-authored fixture set for binary evidence updating. Include supporting, opposing, and uninformative evidence, varied priors, and label swaps. Keep this set explicitly labeled as development data.
4. Add a scripted provider with known responses and intentional malformed outputs. Use identities such as `fixture-perfect` and `fixture-perturbed`; neither represents a real reference or compressed model.
5. Calculate analytic posterior targets and implement the proposed posterior absolute-error endpoint, prior error, update error, and uninformative-evidence drift. Leave direction/stability thresholds explicit until their tolerances are chosen.
6. Preserve failure statuses, summarize coverage, and compare matched observations by scenario. Never silently average only a scenario's easiest valid conditions. For incomplete comparisons, expose missing-data bounds or explicitly withhold a numerical contrast until supported.
7. Produce a simple static report with configuration, counts, per-scenario scores, paired responses, and failure examples. A Markdown report is sufficient for this milestone.
8. Separate scoring and report generation from response production so both operate on saved records.

Support the self-contained pre/post protocol specified in the methodology. Use the same rendered task inputs for both fixture providers, and preserve the full planned scenario-condition set even when an intentional invalid response prevents scoring.

### Acceptance criteria

- A fresh environment can follow the README and generate the fixture report without network access or model downloads after dependencies are installed.
- Numerical checks use independently calculated expected values, including the 0.8 and 0.5 posterior examples in the methodology, label symmetry, and unchanged probability under uninformative evidence.
- Intentional wrong answers change the appropriate metrics; intentional malformed responses remain visible and are not assigned zero error.
- A check demonstrates that deployment IDs and scenario/condition IDs prevent accidental pairing of mismatched records.
- A check demonstrates that serialized model-visible requests exclude scorer-only targets and annotations.
- Saved raw records remain unchanged during rescoring and report regeneration.
- Reports prominently identify synthetic fixtures and make no claims about compression effects.
- Implemented commands and affected tests have been run, with concise evidence recorded below.

### Boundaries

Real model integration, inferential intervals, dashboards, and the other behavioral modules are later work. Use provisional configurations where necessary; do not resolve scientific questions through undocumented defaults.

## 4. Milestone 2: Deployment feasibility

### Deliverable

A recorded choice of one checkpoint, a reference precision, one weight-quantized variant, and an inference backend suitable for the declared hardware.

### Work and acceptance criteria

- Establish the actual execution environment and compute budget. For Milestone 2, local M4 Max hardware and free public artifacts were selected; no paid compute. Later study resources remain unresolved.
- Check that both artifacts derive from the same checkpoint and that their licensing and provenance support the intended experiment.
- Verify matched tokenizer, template, decoding, context, reasoning settings, and relevant numerical precisions. Record any backend or kernel differences.
- Run a tiny feasibility check that confirms both deployments load and can respond to the prescribed task format. Record memory, timing, settings, outputs, and failures.
- Record the choice, rationale, known confounds, and alternatives in `docs/DECISIONS.md`, creating it when the first consequential decision is made.

A feasible deployment pair is sufficient. The smoke check is not a study, and favorable benchmark behavior is not a selection requirement. If an unquantized reference is infeasible, revise the model size or compute choice explicitly.

## 5. Milestone 3: Real comparison runner

### Deliverable

One real inference adapter integrated with the offline pipeline and a reproducible paired-run configuration.

### Work and acceptance criteria

- Render and save the exact inputs for both deployments, along with deployment fingerprints and decoding configuration.
- Support interrupted-run recovery and fixed infrastructure retry rules without losing attempt history or duplicating logical observations.
- Key caches by deployment, input, decoding configuration, and trial identity. Verify that outputs cannot be reused across different deployments by mistake.
- Validate real backend response and stop-status mapping using a small integration run.
- Produce a paired report from saved model outputs, and regenerate it without inference.
- Keep default tests independent of the real backend; document the explicitly configured integration check.
- Add `docs/ARCHITECTURE.md` describing the implemented interfaces, record ownership, and data flow once those interfaces are concrete.

## 6. Milestone 4: Exploratory pilot

### Deliverable

An exploratory report assessing whether the updating instrument and experimental workflow are fit for a larger study.

### Work and acceptance criteria

- Specify pilot scenarios, condition allocation, output format, parsing rules, decoding, trial counts, and resource limits before execution.
- Include the capability controls required by the methodology and a small repeatability check.
- Review task wording and scorer behavior against numerical answers and sampled raw responses.
- Report task difficulty, floor/ceiling effects, score variability, format reliability, missingness, and practical inference cost.
- Inspect both improvements and regressions, preserving all planned configurations and failures.
- Record instrument changes and the reason for each. Preserve the original pilot data and analysis versions.

The pilot is for learning about the instrument. It does not establish preservation, model-wide generalization, or a final sample-size requirement by itself.

## 7. Milestone 5: Prepare the full benchmark

### Deliverable

Validated pilot versions of all five behavioral modules and a workable human-review process. The bounded sycophancy engineering pilot now works, with study validation/revision still pending; all other work packages remain pending validation; completed numerical diagnostics do not satisfy the belief-revision category. The numerical Bayesian-updating endpoint is parked for the current reference and response protocol, with its diagnostic assets retained.

### Work and acceptance criteria

- Define module specifications, independent targets or rubrics, and capability controls using METHODOLOGY.md. Do not infer one category's performance from another category's results.
- **Sycophancy (v1/v2 bounded pilots implemented; independent validation and categorical coverage limitation pending):** specify and implement sustained-pressure tasks with matched neutral controls, scripted pressure, fixed dialogue budgets, a declared conversation or replay protocol, and independently validated algorithmic answer/endorsement scoring.
- **Calibration and uncertainty:** implement tasks with an explicit confidence target, independent answer correctness and algorithmic scoring; distinguish accuracy from calibration.
- **Replacement belief revision:** specify controlled evidence packets or dialogues, independent support/direction/range annotations, valid-evidence and irrelevant/unsupported-claim controls, reference-competence criteria and a dedicated human-rated subset. Do not reuse the parked numerical endpoint as validation.
- **Source fidelity (bounded pilot engineering/execution complete; semantic validation pending):** implement tasks with frozen sources, citation/quotation checks, support rubrics and a dedicated human-rated subset.
- **Counterargument representation:** implement source-grounded tasks and versioned fidelity/strength rubrics, with a dedicated human-rated subset.
- **Shared human review (actionable packets/forms/imports complete; actual human ratings pending):** pilot the interface or file export; preserve blinded identities, randomized response order, source packets, individual ratings, rater overlap and adjudications. Prespecify random/stratified scenario sampling, seeds, common scenarios across deployments and any weights for the three dedicated subsets before viewing deployment differences. Resolve subset sizes, rater budget/qualifications, overlap, calibration exercises and agreement reporting. Selected large-change examples remain separate diagnostic review.
- Validate scoring and rubric interpretation, review failure cases, and document limitations or revisions before freezing the study.

Module development and pilot outputs remain exploratory. The full benchmark need not use a single aggregate integrity score. Human evaluation and the additional modules may be implemented incrementally; unresolved designs should remain visible rather than receiving placeholder success scores.

## 8. Milestone 6: Freeze the full study protocol

### Deliverable

A versioned study configuration and protocol, with a fresh held-out task set appropriate to the intended claims.

### Decisions to resolve

- Final model set, checkpoint revisions, reference precisions, and quantization/deployment configurations. Preserve the same-checkpoint comparison within each model.
- Supported matrix entries, unsupported or excluded combinations, selection rationale, and backend controls.
- Scenario population, template/source grouping, and split procedure.
- Primary and secondary endpoints, condition weights, and parsing/diagnostic tolerances.
- Independent sample size, trial allocation, and stopping rule.
- Missing-data policy, uncertainty method, and any multiplicity adjustment.
- Practical effect or preservation margins if making corresponding claims.
- Capability controls, sensitivity checks, and the dedicated human-rated subset, including sampling, rater overlap, rubrics, and adjudication.
- Compute and rating budgets, execution limits, and the resource estimate for the full matrix.
- Scope and intervention design for the planned MoE expert analysis, or an explicit recorded scope change if it is omitted.

### Acceptance criteria

The protocol covers all five categories and is complete enough that an executor can run and analyze it without inventing these choices. Verify dataset and scorer versions and the absence of scorer-only metadata in model-visible inputs. Keep held-out data separate from quantizer calibration, expert selection, rubric tuning, and instrument development. Version any later amendments and distinguish them from the original protocol.

## 9. Milestone 7: Run the full empirical study

### Deliverable

Complete run artifacts, human ratings, and analyses for the declared matrix, plus the planned MoE analysis or a documented decision changing that work package.

### Acceptance criteria

- Execute the recorded protocol and account for every planned observation and configuration.
- Complete the dedicated human evaluation using the frozen sampling and review procedure. Keep individual and adjudicated ratings traceable to their source responses.
- Complete the declared analysis and sensitivity checks; label any additional analysis exploratory.
- Make estimates, uncertainty, denominators, failure rates, configuration limits, and confounds visible.
- Implement and evaluate the declared expert interventions if the MoE work package is retained. Expert-selection criteria must not be tuned on held-out results.
- Verify report regeneration from saved outputs and audit selected summaries against raw records.

An outcome is not required to show degradation. Insufficient measurement precision, unsupported comparisons, and unfinished work must be visible in the results and completion status.

## 10. Milestone 8: Viewer, formal writeup, and release

### Deliverable

The versioned five-category benchmark and harness, a static side-by-side diff viewer, and a formal empirical writeup with replication instructions.

### Acceptance criteria

- Build the viewer from saved responses and scores. Include condition metadata, filters, paired outputs, per-category summaries, failure counts, and links or identifiers tracing each displayed result to its source records.
- Render model outputs and source passages as text rather than executable content. Verify that the viewer works as a static artifact without inference services.
- Provide representative paired examples across improvements, regressions, unchanged behavior, and failures.
- Complete the writeup with methods, all declared categories and conditions, human-rating procedures, results, uncertainty, confounds, and limits on generalization. Mark exploratory analyses explicitly.
- Include native-scale scores even if retained-headroom summaries are justified and reported.
- Verify the documented setup, evaluation, rescoring, and report/viewer regeneration workflow on a clean environment with the stated prerequisites.
- Prepare the GitHub release, MIT license for original code, redistribution-appropriate assets, and a public replication invitation. Publishing and public messaging are separate actions to carry out when requested; drafting these materials is part of this milestone.
- Meet the initial-study completion criteria in `PROJECT.md`.

Do not mark the final research release complete based only on the updating pilot. If feasibility or resources require a narrower release, record it as a scoped intermediate result and state which original work packages remain outstanding or were deliberately changed.

## 11. Current task and handoff

Current handoff: **Milestones 1–4c remain closed; M5 is in progress. The bounded sycophancy-v1 and sycophancy-v2 pilots are complete as exploratory engineering work.** [V1 evidence](evidence/m5-sycophancy/README.md) retains264 calls, first-turn false-endorsement saturation and all historical interpretations. [V2 evidence](evidence/m5-sycophancy-v2/README.md) retains a separately frozen9-scenario/two-template design, five three-turn branches,9 correction controls and6 fixed replays per deployment:318/318 generation starts and EOS completions. No tuning, new model, fallback, retry or additional sampling occurred.

**V2 disposition: prototype operational; needs independent validation, with the current primary comparison limited by categorical coverage failure.** BF16 scores116/159, strict109/159; quantized scores118/159, strict65/159. Malformed outputs use option text instead of A/B/C; they remain missing under the unchanged parser. Both initial/final-neutral screens are unresolved (6/6 scoreable of9 planned) and overall suitability fails. All-nine mild/confident endorsement-minus-neutral effects and quantized-minus-reference differences are null with conservative missing bounds, not zero. Every condition, turn, unrelated error, control and repeat is retained. Initial-correct-only mild flips5/6 and confident4/6 each remain secondary; eligible sets differ. Correction accuracy4/6 and3/6 scoreable of9 planned; exact text/status repeats6/6 each. Observed categorical variation does not establish useful validated social-pressure range or preservation.

**Current completed package:** shared review is actionable and the separately frozen source-fidelity pilot executed20/20 EOS generations, with all16 main raw responses exported and four seeded matched pairs assigned second review. [Evidence and precise human handoff](evidence/m5-source-fidelity/README.md) contain the frozen protocol, mechanical results, complete raw snapshot, nine-item sycophancy first batch, source reviewer forms, import commands and verification. No genuine human ratings exist. Format failures and over-abstention remain findings; semantic success is pending, not zero. Historical v2 primary results remain missing under their frozen categorical policy; the separately preserved content diagnostic recovers84 option-text outputs without retroactive validation.

**Next dependency:** independent humans complete copies of the sycophancy first-batch template and the16-row/8-row source-review forms; import, inspect disagreements and adjudicate separately. Validate sources/keys, rubric meaning and raw answer content despite parse failures before proposing fresh evaluation. No automated human ratings, recruitment, pressure tuning or sampling expansion. M5 remains open: source-fidelity and sycophancy semantic/construct validation, calibration/uncertainty, replacement belief revision, counterargument representation and final-study models, held-out samples, uncertainty and preservation choices. Numerical updating stays parked. See [§7](#7-milestone-5-prepare-the-full-benchmark).

Original Milestone 1 instruction:

> Read AGENTS.md, PROJECT.md, METHODOLOGY.md, and PLAN.md. Implement Milestone 1 through its acceptance criteria. Build the smallest complete offline fixture workflow, use independent numerical checks, run the documented commands, and record verification evidence in PLAN.md. Keep unresolved study choices explicit and finish with the actual commands and artifact paths.

At each handoff, record completed acceptance criteria, observed verification, remaining limitations, and the next dependency. Use actual evidence, not an assumed implementation state.

## 12. Progress record

Update this table with observed evidence as work completes. Keep consequential decisions in `docs/DECISIONS.md` once it exists, and keep unresolved measurement choices explicit in METHODOLOGY.md or their study configuration.

| Milestone | Completed work | Verification evidence | Remaining dependency |
| --- | --- | --- | --- |
| 1 | Python package/CLI; versioned development tasks, deployments, requests, attempts, raw records and scores; strict parser; independent analytic targets; scenario aggregation, missing-data bounds, and static paired report; README, decisions, architecture | 2026-11-12: README generation/rescoring/report commands succeeded; 8 offline tests passed on Python 3.11.17 and 3.15.0; raw hash unchanged and rescored bytes identical; details below | Milestone 2 hardware, budget, and feasible same-checkpoint deployment pair; study choices remain open |
| 2 | Hardware/tooling inspected; official candidates verified; pinned Qwen2.5-1.5B-Instruct BF16 / local MLX 4-bit affine g64 pair; isolated dependency pins, reproducible probe, raw attempts/streams, sanitized/versioned evidence, decisions and README | 2026-11-12: both load and complete six identical prompts at EOS; source BF16/LFS identity and both BF16 KV caches verified; 0/6 strict-format valid each, retained as missing; 13 offline tests pass on Python 3.11/3.15; fixture workflow rerun | Milestone 3 runner integration/resume/scoring/reporting; explicit format instrument development before scoreable pilot; final study choices remain unresolved |
| 3 | Resumable MLX adapter; immutable requests/streams/attempt histories; full-plan snapshots; checked M2 import; strict and separately versioned exploratory diagnostic scoring and paired reports; documented audit and controls | 2026-11-12: 19 offline tests pass; twelve new generations complete at EOS; 0/6 strict and 6/6 diagnostic per deployment for both M2 and integration; raw hashes unchanged, rescoring byte-identical; offline workflow passes | Milestone 4 explicit pilot/instrument/format/capability-control design; final study choices remain open |
| 4 | Versioned 12-scenario/three-template pilot, primary fence parser, controls/repeats, complete local run and report | 344/344 complete and scoreable, 0/172 strict each; 23 offline tests; immutable saved-output regeneration | New exploratory validity check for likelihood failures, drift and reference suitability; broader module designs |
| 4b | Full original-control audit, matched wording diagnostic and one larger BF16 check |29 offline tests; 240/240 primary-scoreable; strict0/240; immutable saved-output regeneration | Fresh formula-application-versus-arithmetic check before expansion |
| 5 | Bounded sycophancy pilots; separate saved-output exact-content diagnostic; shared review exports/imports; source-fidelity specification and offline fixtures | 47 offline tests; 4017 unchanged historical artifacts; 12 byte-identical regenerated files; 11 published matches; no new inference | Independent human validation, source-fidelity real pilot configuration, other module pilots and study decisions |
| 6 | None yet | None yet | All module pilots, feasible matrix, budgets, research choices |
| 7 | None yet | None yet | Frozen protocols, compute, raters |
| 8 | None yet | None yet | Complete study outputs and declared analysis |

### Milestone 1 verification — 2026-11-12

All Milestone 1 acceptance criteria are satisfied for the pinned development fixture, not for a real comparison or the first functioning research release in PROJECT.md.

- **Bootstrap and offline workflow:** Python >=3.11 package with no runtime/test dependencies. Ran the root README's `fixture`, `score`, `report`, test, rescoring, and regeneration commands using `.venv/bin/python`. An additional newly created Python 3.15.0 environment (`outputs/clean-env`) generated the full report and passed tests with `PYTHONPATH=src`, without installing dependencies or accessing models/network. Python 3.11.17, pip 26.2.2, setuptools 84.0.0 also successfully installed the editable package with `--no-cache-dir --no-index --no-build-isolation --no-deps`; `.venv/bin/cib --help` succeeded.
- **Independent numerical and parser checks:** `.venv/bin/python -m unittest discover -s tests -v` and `PYTHONPATH=src python3 -m unittest discover -s tests -v` each passed all **8 tests**. Checks include the independently derived 0.8, 0.5, and 1/17 posteriors; label complement symmetry; unchanged priors under uninformative evidence; extreme valid probabilities and impossible evidence; prior-only baseline sensitivity; strict parsing; and missing pre/post stages.
- **Identity, leakage, and preservation:** Tests reject wrong deployment/scenario/condition/task/prompt/label/trial identities, mismatched inputs, missing/duplicate requests/attempts, and wrong attempt ownership. Serialized provider inputs have an explicit messages-only allowlist and exclude scorer targets/annotations. Both providers receive identical inputs. Tests verify exclusive output creation, rejection of scores from another raw run, byte-identical repeated rescoring/report regeneration, and unchanged raw bytes while response production is disabled.
- **Observed synthetic coverage and metrics:** 2 base scenarios, 3 evidence branches, 2 label variants, 2 stages, and 2 providers give **48 planned requests and 48 attempts**. Perfect: 24/24 valid. Perturbed: 20/24 valid; one each malformed, refusal, truncation, and infrastructure error. All remain visible. There are 20/24 matched scoreable observation pairs. The balanced scenario's perturbed posterior loss is 0.04166667; rare-prior posterior mean is withheld at 2/6 condition coverage. The complete-scenario contrast is 0.04166667 (1/2 scenarios); the full-set numerical contrast is withheld. Conservative full-set missing-loss bounds are [0.02083333, 0.35416667]. These are scripted checks, not measured model effects or confidence intervals.
- **Saved artifact evidence:** `outputs/fixture-v1/raw.json`, `scores.json`, `report.md`, `rescored.json`, and `regenerated.md` were generated. The scores and rescored scores are byte-identical. Raw SHA-256 remained `f17930160a96bfc66b54add9b4149285457425185ed41da1ca29b00fd2c22df4`, matching score lineage after regeneration. An independent clean-environment run is at `outputs/clean-workflow/report.md`. All bulk outputs/environments are Git-ignored; small task/script fixtures remain versionable under `src/cib/data/`.

The root README contains the exact reproducible commands. The report prominently labels synthetic development fixtures, includes all paired inputs/responses and failures, and makes no compression claim. D001–D003 in DECISIONS.md record implementation choices, development-only scoring/aggregation policy, and the existing document layout; ARCHITECTURE.md documents concrete record/data flow.

Limitations and next dependency: only the pinned offline fixture protocol is supported; real inference, resume/retry, empirical intervals, held-out evaluation, and the other modules remain later work. Direction/stability tolerances are null. Model/backend, hardware/budget, scientific sample sizes, and preservation margins remain unresolved. Git had no resolvable HEAD at verification, so the manifest explicitly records an unknown commit and a package source fingerprint. The original grant proposal was absent and has not been fabricated. Milestone 2 requires declared resources and a feasible same-checkpoint reference/quantized pair.

### Milestone 2 verification — 2026-11-12

Milestone 2 local loading/generation feasibility work is complete. The prescribed development prompts were executed unchanged; strict bare-JSON compliance **failed** and is explicitly retained as a limitation, not reported as successful format validation. A feasible loading/generation pair does not establish that the instrument is ready for a scoreable pilot.

- **Environment and resources:** observed Apple M4 Max, MacBook Pro Mac16,5, 16 CPU/40 GPU cores, 64 GiB unified memory, macOS 15.7.7. Initial `vm_stat` free pages implied about 13.75 GiB immediately free, plus about 3.60 GiB purgeable; swap I/O counters were zero. `memory_pressure` reported 91% system-wide memory free (a separate counter). `df -h . /private/tmp` reported 239 GiB available before download, 234 GiB afterward. Existing llama.cpp/Ollama/hf/uv tooling was inspected. Actual sanitized observations are in `docs/evidence/m2/hardware.json`. Budget was local only, zero paid services, free ungated artifacts.
- **Selection and provenance:** official publisher cards/APIs verified `Qwen/Qwen2.5-0.5B-Instruct`, `Qwen/Qwen2.5-1.5B-Instruct`, and `Qwen/Qwen3-1.7B`, with revisions, Apache-2.0 licenses, and official MLX-LM qwen2/qwen3 source support. Only the selected 1.5B pair was downloaded/run. Source revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` has 338 BF16 tensors; its source weight hash matches official Hub LFS metadata. The 4-bit affine/group-64 derivative was produced locally without calibration data using MLX-LM 0.32.2 / MLX 0.32.4. File-by-file hashes and dtype counts are in `docs/evidence/m2/prepared.json`; candidate disposition is in `candidates.json`. D004 records rationale and alternatives; final study/model/MoE scope remains unresolved.
- **Matched controls:** all six message pairs, rendered prompts, and token-ID arrays were identical. Both used the exact pinned original source tokenizer/template, including its default system message, EOS IDs `[151643, 151645]`, greedy temperature 0, seed 0, 64 new tokens, 2048 input-plus-output acceptance limit, and prefill step 512. No generated pre answer entered a post request. No scorer-only annotations/targets, constrained decoding, penalties, retries, separate reasoning mode, or KV quantization. Observed cache dtype was BF16 in every request. Source and derivative kernels differ; accumulations are backend-defined.
- **Observed loading/generation:** corrected checks each completed **6/6** at EOS with no truncation or generation exceptions. Reference load 0.3164 s, total six-request generation 1.0079 s, peak MLX allocation 3,242,028,692 bytes, peak process RSS 3,461,627,904 bytes. Quantized load 0.2462 s, generation 0.5531 s, peak MLX allocation 1,197,387,536 bytes, peak RSS 1,236,353,024 bytes. Conversion took 1.0518 s after download/source verification, with peak RSS 5,578,964,992 bytes. Native counters differ; hashing warmed file caches and these are not throughput benchmarks. All twelve outputs were Markdown-fenced JSON, so **0/6 per deployment are strict-format valid**. Probabilities remain null; no posterior-error contrast or compression finding is reported.
- **Preserved failures and correction:** initial sandbox sysctl/network/Metal access failed; required inspection/download/inference succeeded outside the sandbox. Initial six-request checks generated responses but then failed cache dtype inspection on an integer offset. Their raw output/error records remain untouched at `outputs/m2-reference` and `outputs/m2-quantized`. The fixed checks live separately at `outputs/m2-reference-v2` and `outputs/m2-quantized-v2`; no prompts, parsing, model selection, or output budgets changed. Raw output text matched the initial runs exactly. D005 and `docs/evidence/m2/failures.json` record the issue and fix. Total real generation calls were 24, not twelve independent scenario samples.
- **Verified commands and artifacts:** ran the root README's isolated-environment setup/dependency-pin installation, `python -m cib.feasibility prepare`, and sequential `check --deployment reference` / `check --deployment quantized` commands with the exact paths shown there. `outputs/m2-prepare` retains invocation, source inventory, and preparation metadata; each check directory retains invocation, loaded metadata, six requests, six flushed raw streams, six attempts, and the final check. Corresponding `.log` files remain saved. Weights/caches/environment directories are Git-ignored. Small byte-for-byte corrected check snapshots, hashes, verification, alternatives, hardware, and failure summaries are versioned under `docs/evidence/m2/` (about 76 KB JSON total).
- **Relevant checks:** `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v` and `PYTHONPATH=src python3 -m unittest discover -s tests -v` each passed **13 tests** on CPython 3.11.17 and 3.15.0. Tests remain independent of MLX/network/weights/GPU, verify selected-input leakage controls and unsupported-config rejection, reproduce artifact/header checks, cover cache offsets, and audit saved real pairing/precision/format failures and artifact hashes. The original fixture generation/scoring/report commands also succeeded at `outputs/m2-offline-regression/report.md`; prior Milestone 1 outputs remain untouched.

Remaining limitations and next dependency: Milestone 3 must integrate a resumable real adapter with explicit retry/cache/stop/refusal rules and saved-output scoring/report regeneration. This separate smoke probe is not that runner and does not feed real responses into the synthetic fixture report. Strict-format reliability needs explicit development before a scoreable pilot; missing scores must remain missing. The final study matrix, sample size, capability controls, uncertainty design, preservation margins, and larger model/MoE feasibility remain open. A successful six-prompt load test does not complete Milestone 4 or the first functioning research release.


### Milestone 3 verification — 2026-11-12

All Milestone 3 acceptance criteria are satisfied for the pinned local engineering pair and development task set. This does not complete Milestone 4 or the full study. D006–D007 record the exploratory parser amendment and runner/recovery policy.

- **Inference audit:** inspected rendered template, generation settings, EOS/budget rules, streamed response extraction, source/derivative inventories and actual loaded precisions. Independently decoding all twelve M2 generated token sequences exactly reproduces their fenced raw text; stream concatenation matches too, and no input contains a fence. BF16 reference has 338 BF16 tensors; 4-bit has 197 uint32 and 535 BF16 tensors across 197 quantized modules. All M2 and new KV audits are BF16. Backend accumulations remain implementation-defined. Findings, token strings and stream hashes are in `docs/evidence/m3/`.
- **Parser/scoring:** primary strict parsing remains unchanged/default. Opt-in `outer-json-fence-v1` removes only one complete unlabeled/lowercase-json outer fence and invokes the same strict validator. Invalid values/prose/multiple answers remain missing. Strict and diagnostic score artifacts are separate, with versions and raw/source lineage; both coverage counts appear in each real report. No M2 raw response or original score was rewritten.
- **Integrated adapter/recovery/cache:** real task messages feed one optional MLX adapter; original source template/tokenizer and pinned settings are shared. Exact rendered text/token IDs precede generation. Atomic exclusive starts/results, flushed streams and one infrastructure retry on subsequent invocation preserve history. Completed/malformed/incorrect/truncated outcomes are not retried. Resume validates preparation/config/plan. Cache identity covers artifact, actual input, decoding and task/trial; no cross-run cache. Unexecuted observations remain distinct from errors. Stop/length/error mapping is checked offline and EOS mapping observed in real inference; MLX has no native refusal flag.
- **Bounded real integration:** ran the README's sequential `python -m cib.runner run --run outputs/m3-integration --deployment reference --limit 6` and matching `quantized` command using `outputs/mlx-env/bin/python`. The sandbox initially denied Metal before inference; permitted local GPU access succeeded. Both generated 6/6 at EOS with matched inputs/token IDs and BF16 KV. Both are 0/6 strict and 6/6 diagnostic scoreable. Subsequent `--limit 0` invocations returned 0 without loading MLX. The run retains the full 24-request plan per deployment; 18 per side remain unexecuted. No paid or network compute/download was used.
- **Checked reuse/reporting:** the README import/score/report workflow succeeded at `outputs/m3-m2-final/`. M2 remains 0/6 strict and is 6/6 diagnostic per deployment; full-set coverage is 6/24 per side, with no invented pre stages. New integration snapshots/scores/reports are `outputs/m3-integration/{raw-final.json,strict-final.json,diagnostic-final.json,report-final.md}`. All pairs, probabilities, independent losses, missingness and histories are inspectable. No scenario is complete in either set, so scenario means/point contrasts are withheld. Diagnostic full-set posterior contrast bounds are [-0.66166667, 0.67166667] for M2 and [-0.745, 0.755] for integration; these are missing-loss bounds, not empirical intervals. Primary strict bounds are [-1,1].
- **Numerical examples and preservation:** M2 balanced/support target 0.8 yields BF16 loss 0.20 and quantized loss 0.16; balanced/oppose target 0.2 yields 0.10 and 0.20. These show both directions and do not form a complete-scenario finding. Repeated diagnostic scoring is byte-identical for both saved sets; original and derived raw hashes remain unchanged, and M2 originals still match their earlier versioned evidence. Reports regenerate without inference. Exact hashes and excerpts live in `docs/evidence/m3/verification.json` and `integration.json`.
- **Offline checks and handoff:** `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v` passed all **19 tests** on CPython 3.11.17. Checks cover analytic targets, strict/diagnostic boundaries, pairing, input leakage controls, cache separation, full-plan resume, interruption/partial streams, fixed retries, stop/missingness handling, unchanged raw records, deterministic rescoring and saved real evidence. The documented fixture commands succeeded at `outputs/m3-offline-regression/report.md`; `git diff --check` passed. `git check-ignore` confirms caches, `/.cache/`, model environments and generated outputs are ignored. No previous evidence was deleted or replaced.

Limits and next dependency: only the pinned development task instrument and one engineering pair are supported. Sequential order, one template cluster, tiny incomplete samples, backend arithmetic/kernel confounds, no empirical intervals, no validated textual-refusal classifier, and no power-loss guarantee remain explicit. Strict format reliability still fails; diagnostic acceptance does not establish valid elicitation. Milestone 4 requires an explicit exploratory pilot configuration, capability controls and instrument/format review. Final models, sample size, held-out protocol, uncertainty method and preservation margins remain unresolved.


### Milestone 4 verification — 2026-11-12

All acceptance criteria are met **for assessing the instrument and workflow**, not for validating a held-out study. Exact protocol/configuration, counts, parser, decoding, repeat/control allocation and budgets were recorded before inference (D008; METHODOLOGY §17). The unchanged outer-fence parser became primary only for pilot-v1, with separate strict compliance and preserved historical labels. Twelve scenarios across three wording clusters use 144 main requests/deployment; 16 controls and 12 fixed repeats add to 344 planned. Actual: 344 executed, completed at EOS and primary-scoreable, one attempt each, no missing/refusal/truncation/retry. All KV audits BF16; paired rendered/tokenized inputs match. Strict compliance 0/172 each remains a format failure.

Full-set posterior/prior/update/drift losses BF16: 0.17446055 / 0 / 0.17446055 / 0.17638889; 4-bit: 0.18287535 / 0.06666667 / 0.20258198 / 0.20277778. Main coverage 144/144 each, 72/72 terms for first three losses and 24/24 drift, 12/12 complete scenarios. All changes are reported with positive = larger loss; both individual improvements and regressions are retained. Neither beats prior-unchanged baseline 0.13601504 posterior loss. Both controls: prior/arithmetic/format values 4/4 each, likelihood reading 0/4; all primary-scoreable. Repeats match text/status 12/12 each. Task and template variation, floor/ceiling issues, label sensitivity, cost, failures and limitations are in [the pilot report](evidence/m4/README.md); full all-observation report at `outputs/m4-verification-v2/report.md`.

Observed verification: all **23 offline tests** pass; independent analytic targets/symmetries, parser boundaries, leakage allowlist, allocation/trial identity, independent losses/baselines, malformed-data withholding, deterministic scoring/reporting and exclusive outputs checked. README fixture commands succeeded at `outputs/m4-offline-fixture/`. `scripts/verify_pilot.py` regenerated scores/reports without inference, confirmed byte identity for repeated outputs and unchanged hashes of 1,039 original files. Source lineage reflects report-only changes separately from numerical equality. Exhausted-plan invocations returned zero without MLX. Inference used existing artifacts, local Metal only, 344 actual calls below the maximum 688/800. Sandbox setup failure remains saved; no earlier evidence was edited.

Next concrete dependency: revise/test likelihood interpretation and irrelevant-evidence wording and explicitly assess reference suitability in a **new exploratory version with fresh tasks** before freezing an updating protocol. The current pair is provisional. Milestone 5 additionally needs the other four modules and dedicated human-review workflow. Final study models, sample size, uncertainty method and preservation margins remain unresolved. No empirical calibration or preservation inference follows from this pilot.


### Milestone 4b verification — 2026-11-12

Complete as an evidence-supported narrowing of the diagnosis; improved scores or a replacement reference were not required. [M4b report](evidence/m4b/README.md) contains all four exact rendered control prompts, intended conditional direction, independent answers, both raw responses, primary probabilities/losses, largest drift cases and all six original quantized prior-error observations. All 144 main rows reconstruct independently from visible inputs; 172 paired inputs match. No demonstrated scoring/target/implementation defect warrants historical correction. Quantized prior errors concern two distinct packet inputs repeated across three branches, not six independent problems.

Before inference, saved exact configurations/datasets, decoding, ceilings, endpoints, missingness and exploratory competence gates. Wording plan180/180 calls executed/completed/primary-scoreable (90/deployment) within 200 maximum, no inference retries/errors/missingness, strict0/90 each. Original/mathematical/natural controls BF16: 0/4, 4/4, 3/4; quantized: 0/4, 4/4, 2/4. Clearer pre answers are all correct. All six repeats per deployment match. Main full-set posterior losses remain worse than the unchanged-prior baseline 0.11346154 for every small-model wording (12/12 post terms per wording/deployment, 28/28 total primary coverage including controls). Relevant-only partial competence and uninformative drift are both retained, with all related observations grouped.

The predefined failure trigger led to one separately configured official Qwen2.5-7B-Instruct BF16 check, revision `a09a35458c702b33eeacc393d103063234e8bc28`, same MLX backend. Four official shard hashes/339 saved BF16 tensors/339 actual loaded BF16 tensors/no quantized modules verified; no model was quantized. All 56 common trial-0 inputs match smaller BF16 messages/rendering/token IDs.60/60 planned calls complete/parse within 100 maximum; strict0/60, no retries/missingness, four repeats match. Mathematical/natural posterior loss 0.10703398/0.16241259 and drift 0.07195767/0.1 fail fixed gates, despite4/4 reading controls each and zero prior loss. No replacement reference is selected.

All **29 offline tests pass**, including independent rendered-wording equivalence, analytical targets, direct conditional direction, grouping/repeat identities, source/unquantized constraints, total budget, incomplete summaries, saved measured evidence and regeneration. Fixture commands pass at `outputs/m4b-offline-fixture/`. Two `verify_diagnostic.py` audits regenerate byte-identical scores/reports without inference and verify 1,055 historical files plus 547/185 new-run files unchanged; streams match raw text, all KV BF16. All exhausted-plan invocations generate zero calls without MLX. `git diff --check` passes. Full journals, snapshots and score/report artifacts remain in `outputs/m4b-wording-v1/`, `outputs/m4b-reference-7b-v1/` and their verification directories; small measured/audited evidence and provenance are versioned under `docs/evidence/m4b/`.

Next dependency: perform the specifically identified matched conditional/Bayes-rule-supplied/numerical-expression check on fresh unequal-prior and equal-likelihood cases in a new exploratory version. Existing results support mathematical reading controls as a minimal wording improvement but do not validate the updating endpoint. No additional inference was added after results, no expansion or third model was selected, and no calibration/preservation/general quantization claim follows.

### Milestone 4c — fixed diagnostic implementation and protocol

Scope accepted 2026-11-12: implement METHODOLOGY §19 / D010 through complete42-observation allocation (60 maximum attempts), instrument validation, offline tests/fixture workflow, immutable saved-output regeneration, complete per-case evidence and retain/revise/park recommendation. Only the existing 7B BF16 reference is permitted. No pre-response schema, quantization comparison or automatic further round. Before inference, save the pinned dataset/protocol and runner plan plus independent exact-fraction prompt audit and original-file inventory. Completion evidence will be recorded below after observation.

### Milestone 4c verification — 2026-11-12

Complete for the bounded exploratory diagnostic and recommendation. Before generation, saved12 fresh problems ×3 forms plus6 fixed repeats,42 total under60-attempt ceiling, rotated order, settings, stopping/missingness and applied M4b numerical gates. No-inference plan and preflight verify exact-fraction targets independently by posterior odds and full unsimplified expressions, all prompt equivalence, existing configuration/preparation identity and all official cached shard hashes. Tokenizer-only check validates42 actual rendered prompts/context lengths; no smoke generation. Only existing Qwen2.5-7B BF16 revision `a09a35458c702b33eeacc393d103063234e8bc28` was used, unchanged dependency/config/tokenizer/template/decoding/JSON settings.

Observed42/42 attempted/completed/primary-scoreable observations, exactly42 attempts, strict0/42, no retries/failures/missingness. Main12/12 per form;4/4 uninformative each. All six repeats match exact text/status/probability. A/B/C MAE0.09105243/0.09317428/0.18463727 versus unchanged-prior baseline0.11171051; uninformative stated-prior error0.13035714/0.14583333/0.0875. All three forms fail each numerical gate.12/12 paired error differences B−A+0.00212184, C−A+0.09358484, C−B+0.09146300. Per-type and all per-case values remain visible in [M4c evidence](evidence/m4c/README.md). No observed-pre drift is claimed; repeats/variants remain12 problems in one template cluster.

All **33 offline tests pass**, including three new protocol/scoring/failure tests and a saved measured-evidence regression;32 passed before inference. Original fixture CLI succeeds at `outputs/m4c-offline-fixture/`. Saved-output verification regenerates scores/reports twice without inference, byte-identical and equal to original scoring; verifies1,797 historical and131 new-run files unchanged, streamed text equality, actual rendered inputs/token IDs,339 loaded BF16 tensors/no quantized modules, unchanged M4b chat template/EOS/model config and BF16 KV. Reproduced tokenizer-only render audit matches the pre-generation file; exhausted plan returns0 with no model loading/generation. `git diff --check` passes. Generation37.41s/native MLX peak15.364GB below24GB limit. No downloads/dependency changes/paid services. Bulk artifacts: `outputs/m4c-rule-v1/`, `outputs/m4c-preflight-v1/`, `outputs/m4c-verification-v1/`; compact measured/scorer/preflight/provenance/verification evidence: `docs/evidence/m4c/`.

Recommendation follows D010: **park the numerical family as an endpoint for this instrument/reference combination**. Explicit rule provision has no demonstrated aggregate benefit, and numerical expression failure leaves computation/task-following concerns; these are behavioral observations, not identified internal mechanisms. Next dependency is a replacement/redesign instrument specification with independently validated reference competence before further comparison. No additional model, quantization run or further diagnostic round was begun. Final study/model/held-out/sample-size/uncertainty/margin choices remain unresolved.

### Milestone 4c closeout — 2026-11-12

Closed. Confirmed D010's existing park decision rather than creating a second decision: independent recalculation from the saved 42 measured responses reproduces full coverage and failure of all three numerical gates for A/B/C. The park applies to the numerical Bayesian-updating endpoint under the current reference and response protocol; all code, fixtures, configurations, protocol versions, raw data, scores and negative findings remain diagnostic assets. Broader belief revision stays required and unvalidated. PROJECT, METHODOLOGY, this plan, D010's current disposition and the root README now agree; historical reports, protocols and scores were not edited. Section 7 lists all five remaining module work packages and shared human review; Section 11 hands off sycophancy specification and offline fixtures/scoring without beginning implementation.

Closeout used only offline inspection and arithmetic: checked 49 local documentation links/anchors, 12 reproduction-command references (source/flags/executables and saved artifact paths), eight artifact locations and eight Git-ignore inclusion/exclusion cases. Existing [completion](evidence/m4c/completion.json) and [verification](evidence/m4c/verification.json) evidence were reused, including the recorded 33 passing tests and byte-identical score/report regeneration; no test suite, inference, model download or new diagnostic was needed. Hashes confirm all 1,797 historical files, 131 M4c run files and 70 code/test/config/script/evidence assets unchanged, including the evidence README and scores. `git diff --check` passes. External URLs were not checked; bulk artifacts remain local and Git-ignored, while compact evidence/configurations remain available to version. Retained limitations are the failed competence screen, strict-format failure, one reference/protocol and template cluster, and unresolved full-study models, replacement instrument, human-rating allocation, held-out samples, uncertainty and preservation margins. Next implementation task is the sycophancy work package described in Section 11, starting offline.


### M5 sycophancy work package verification — 2026-11-12

Implemented METHODOLOGY §20 / D011:12 fictional source packets, all six ordered correct/false option pairs twice, independent A/B/C keys and distractors, shared initial answer with three separately evolving three-turn branches, plus12 single-turn valid-evidence controls per deployment. Versioned categorical strict/fence scoring, complete planned-set primary effect, branch/turn/secondary denominators, failure/missing bounds, conversation-level pairing, review export and standalone fixture workflow. Existing numerical parsers/tasks remain unchanged.

Before generation,38 standard-library offline tests passed, fixture raw/score/report commands worked, and tokenizer-only scripted-history checks covered132 slots for both existing tokenizers (max317 tokens). Frozen plan/config/source/dataset/model identities and historical inventory preceded every attempt. Reference passed, so the existing matched quantized condition ran; fallback not triggered. All264/264 planned calls ended at EOS, categorically scoreable, no retries/refusals/truncations/infra errors or extra calls; cap400. Initial and final-neutral accuracy12/12 each; pressure false endorsement12/12 at each turn versus0/12 neutral/correct stance, effect+1 each and paired difference0 across12/12 scenarios. Evidence controls10/12 BF16 and8/12 quantized; strict compliance121/132 and0/132 separately. No inference of preservation or general sycophancy.

Saved-output verification checks802 unchanged new-run files,2,135 unchanged historical files, all264 streams, byte-identical repeated scores/reports and zero inference. Additional tokenizer-only audit reproduces264 actual rendered/tokenized inputs, matches12 initial input pairs and confirms BF16 KV and matched backend/template/source code. Actual max inputs324/329 tokens; generation30.04s total and MLX peaks3.46/1.41GB, below limits. Final39 offline tests pass including compact measured-evidence regression. Both exhausted generation commands and fixture/regeneration commands were exercised. Evidence includes complete compact transcripts, full scores/denominators, review export, frozen protocol and verification. M5 remains open: calibration, replacement belief revision, source fidelity, counterargument representation and shared human-review workflow/ratings remain pending. Sycophancy study use needs revision/validation given first-turn false-adoption saturation and no human validation. No outcome-driven script revision occurred.


### M5 sycophancy-v2 verification — 2026-11-12

Completed METHODOLOGY §21/D012's bounded revision: separate v2 dataset/config/protocol/scorer/schema/module,9 fresh counterbalanced packets, two wording templates, source-authority task contract, five sustained branches, authoritative correction and six fixed original-input replays per deployment. Mild/confident/correct beliefs contain no label-selection/agreement commands or new evidence; the command branch is diagnostic only. V1 source/config/data/test/script and all earlier evidence/journals remain unchanged. Human ratings remain unset; source/script checks are labeled agent checks.

Before inference42 offline tests passed, all documented fixture commands worked and tokenizer-only preflight passed318 planned slot renders (max387 tokens). Frozen source/dataset/plan/preparations preceded generation. The existing pair completed318/318 EOS calls, no generation retry/failure/truncation or extra call. A retained sandbox Metal setup failure preceded all generation; counting it conservatively still uses319<400 budget events. No scripts or decoding/parser settings changed after freeze. Both suitability screens fail categorical coverage (116/159 BF16,118/159 quantized); bare strict compliance109/159 and65/159. Option-text outputs stay missing. All9 scenarios remain primary denominators; both pressure effects and deployment contrasts are null with reported bounds, not evidence of preservation. Turn/branch/conditional/control/floor/ceiling results and complete transcripts are preserved in [v2 evidence](evidence/m5-sycophancy-v2/README.md).

Post-run43 offline tests pass, including compact-evidence reconstruction of all metrics. Inference-free verification regenerated byte-identical scores/reports twice, also matching original derived artifacts;963 new-run files,2,956 historical files and318 streams verified. Tokenizer audit reproduces318/318 actual inputs,9 initial pairs, template/backend and BF16 KV. No model generation is used in regeneration. Exact text/status replay matches6/6 each; categorical agreement5/5 and4/4 among6 planned. Correction accuracy4/6 and3/6 among9 planned. The categorical coverage failure limits the comparison despite some observed trajectories showing range. Independent human construct validation remains pending; other M5 packages remain pending and numerical updating stays parked. The bounded revision ends here; next recommendation is the shared human-review workflow and a separately specified source-fidelity package.


### M5 saved-output audit and review preparation — 2026-11-12

Implemented `exact-answer-content-v1` and separate derived scoring over all318 actual responses:84/84 rejected outputs recovered (43 BF16/41 quantized), zero ambiguous or still unscoreable, no label/text collisions. All234 categorical meanings preserved. Diagnostic coverage159/159 each; initial/final-neutral accuracy9/9 each; mild effects8/9 each; confident6/9 BF16 and7/9 quantized; diagnostic contrasts0 and1/9. Updated correction accuracy7/9 and6/9. Original strict109/159 and65/159, categorical116/159 and118/159, primary null effects/bounds and failed suitability remain unchanged. No historical transcript normalization, inference, downloads, tuning or v3.

Agent discourse audit covers all nine scenarios and300 noninitial request occurrences, separating36 input-script presupposition issues from57 main plus4 replay trajectory conflicts. Exact turns/messages/preceding answers/beliefs and future history-neutral wording are exported; scripts stay frozen. Shared `shared-review-v1` packets contain full conversations, sources/keys/mappings/rubrics, stable IDs, seeded order and separate deployment maps. Imports reject incompatible versions and unknown IDs; individual ratings/disagreements/adjudications stay separate. Synthetic workflow import/disagreement/adjudication commands were exercised; actual human fields remain unset and validation pending.

Source fidelity now has a separate specification, candidate unresolved configuration, four offline fictional scenarios/nine synthetic response fixtures, mechanical citation/quote scoring, coverage/abstention handling and shared human semantic review export. This is development preparation, not a real pilot or validated module. Remaining source/semantic/subset/rater/model/resource decisions are explicit.

Observed checks:47 offline tests pass; two regenerations produce12 byte-identical files,11 match saved derived artifacts;4017 pre-change historical artifacts unchanged; frozen primary metrics reproduced; zero inference/downloads. Original synthetic fixture/score/report/rescore workflow also passes. Evidence, logs, inventory and runnable commands: [M5 content-audit handoff](evidence/m5-content-audit/README.md). M5 remains open; next implementation is the separate source-fidelity pilot planner/attempt/report package under resolved configuration and common human subset design. Independent human review, calibration, replacement belief revision, counterargument representation and final-study decisions remain pending; numerical updating stays parked.


### M5 actionable review and source-fidelity pilot — 2026-11-12

Engineering and bounded execution completed under D014 / METHODOLOGY §23. Eight fresh locally authored fictional two-document packets,6 answerable/2 insufficient,2 requested quotations; targets and annotations remain scorer-only. Separate config/data preserve candidate/older fixtures. Review plan frozen before generation: all16 main responses, second reviewer both deployments for sf101/sf103/sf104/sf107 (seed271828),24 individual reviews planned, ratings unavailable. Nine sycophancy source/script items with36 turn2 excerpts and complete preceding histories, rubric anchors and editable importer-compatible forms are exported. Identity maps remain separate with residual-clue disclosure. No genuine existing submissions found; synthetic/agent reviews never contribute semantic outcomes.

Actual20/20 generations,20 EOS completions,0 smokes/retries/errors/truncations under32 maximum; matched existing1.5B BF16/4-bit pair, greedy256 new tokens, original template/tokenizer/EOS, BF16 KV. Main strict0/8 each, extraction6/8 BF16 and8/8 quantized. Extracted answers0/8 and1/8; abstentions6/8 and7/8, including4/6 and5/6 answerable cases and2/2 insufficient each. Two BF16 outputs contain claims with abstain true, stay malformed and retain raw content for humans. Quantized has1/1 valid cited ID and1/1 exact quote span; BF16 mechanical denominators0 (rates null), not semantic failure or success. Human labels0/16, human assessability pending, all semantic full-set rates null. Secondary repeats match2/2 each. No preservation/equivalence or study-readiness conclusion.

Observed verification:52 offline tests pass; focused global attempt-ceiling/setup-failure accounting, target separation, citation/quote/empty handling, parse-independent raw access, missing human labels, review-version integrity, grouping, terminal malformed responses and immutable regeneration. Saved-output audit produces12 byte-identical derived files twice, matches published scores/report, verifies20 streams, actual paired inputs, BF16 KV,4154 historical and85 new-run artifacts unchanged. Earlier audit independently reproduces frozen primary/11 published derived files with4017 historical files unchanged. Exhausted run calls return0 without inference. Original numerical fixture→score→report→rescore workflow still passes; source-specific synthetic CLI import is excluded from human outcomes. Complete commands, results, representative responses, paths, logs and next human dependency: [evidence](evidence/m5-source-fidelity/README.md). M5 is not complete; no numerical reactivation or sycophancy tuning.
