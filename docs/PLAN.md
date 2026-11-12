# Compression Integrity Bench: Development Plan

Status: Working implementation plan, v0.4; Milestone 1 verified  
Updated: 2026-11-12  
Project: Compression Integrity Bench (CIB)  
Repository filename: `PLAN.md`

This is the development roadmap for evaluating how quantization changes the epistemic behavior of open-weight language models. It covers uncertainty calibration, resistance to sustained sycophancy, evidence-sensitive updating, source fidelity, and counterargument representation. The intended research outputs are the benchmark and evaluation harness, a static side-by-side comparison viewer, and a formal writeup.

## 1. Starting position

The project owner has reviewed [PROJECT.md](PROJECT.md) and [METHODOLOGY.md](METHODOLOGY.md) and is satisfied with them as working specifications. Their explicitly proposed scientific choices remain provisional.

The initial repository contained specifications and no implementation. Milestone 1 now has an implemented and verified offline fixture pipeline; evidence is recorded in Section 12. No real model runs or benchmark findings are implied. Later milestones remain pending.

Keep AGENTS.md in the repository root and PROJECT.md, METHODOLOGY.md, and PLAN.md in `docs/`, matching the existing layout and links. Retain the original grant proposal unchanged as `docs/original-proposal.md` when supplied; it was absent at bootstrap. Root README.md describes the verified setup and workflow. Scientific requirements live in METHODOLOGY.md; this plan sequences their implementation and does not override them.

The immediate objective is to make one complete example work: construct tasks, obtain clearly synthetic responses, retain records, calculate scores, compare outputs, and regenerate an inspectable report.

## 2. Milestone sequence

| Milestone | Outcome | Main dependency | Status |
| --- | --- | --- | --- |
| 1. Offline pipeline | An auditable example runs without model access | Current specifications | Complete — verified 2026-11-12 |
| 2. Deployment feasibility | One reference/quantized pair is chosen and can run | Declared hardware and resource budget | Pending |
| 3. Real comparison runner | Matched model runs can be resumed, rescored, and compared | Milestones 1 and 2 | Pending |
| 4. Exploratory pilot | The instrument and practical workflow are assessed | Real runner and explicit pilot configuration | Pending |
| 5. Full benchmark preparation | All five modules and the dedicated human-review workflow are piloted | Validated pipeline and explicit module designs | Pending |
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

- Establish the actual execution environment and compute budget. Local Apple hardware and rented accelerators are possible routes; neither is selected by this plan.
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

Validated pilot versions of all five behavioral modules and a workable human-review process. This expands beyond the initial numerical updating pilot.

### Work and acceptance criteria

- Define module specifications, independent targets or rubrics, and capability controls using METHODOLOGY.md. Do not infer one category's performance from another category's results.
- Implement calibration and uncertainty tasks, including an explicit confidence target and algorithmic scoring.
- Implement sustained sycophancy tasks with neutral controls, scripted pressure, fixed dialogue budgets, and a declared conversation or replay protocol.
- Extend evidence-sensitive updating beyond exact numerical cases to a dedicated human-rated subset of broader tasks.
- Implement source-fidelity and counterargument tasks with frozen sources and versioned rubrics.
- Pilot the human-rating interface or export format. Preserve blinded response identities, source packets, individual ratings, overlap, and adjudication records. A simple file-based workflow is sufficient.
- Establish prespecified sampling for the dedicated human-rated subset across updating, source fidelity, and counterargument representation. Diagnostic examples selected for large changes are a separate review set.
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

Current handoff: **Milestone 1 complete: offline fixture pipeline verified.** No model choice, model download, paid inference, GPU rental, or final scientific threshold was selected. The next dependency is Milestone 2: declared hardware/budget and deployment feasibility.

Original Milestone 1 instruction:

> Read AGENTS.md, PROJECT.md, METHODOLOGY.md, and PLAN.md. Implement Milestone 1 through its acceptance criteria. Build the smallest complete offline fixture workflow, use independent numerical checks, run the documented commands, and record verification evidence in PLAN.md. Keep unresolved study choices explicit and finish with the actual commands and artifact paths.

At each handoff, record completed acceptance criteria, observed verification, remaining limitations, and the next dependency. Use actual evidence, not an assumed implementation state.

## 12. Progress record

Update this table with observed evidence as work completes. Keep consequential decisions in `docs/DECISIONS.md` once it exists, and keep unresolved measurement choices explicit in METHODOLOGY.md or their study configuration.

| Milestone | Completed work | Verification evidence | Remaining dependency |
| --- | --- | --- | --- |
| 1 | Python package/CLI; versioned development tasks, deployments, requests, attempts, raw records and scores; strict parser; independent analytic targets; scenario aggregation, missing-data bounds, and static paired report; README, decisions, architecture | 2026-11-12: README generation/rescoring/report commands succeeded; 8 offline tests passed on Python 3.11.17 and 3.15.0; raw hash unchanged and rescored bytes identical; details below | Milestone 2 hardware, budget, and feasible same-checkpoint deployment pair; study choices remain open |
| 2 | None yet | None yet | Hardware, budget, deployment feasibility |
| 3 | None yet | None yet | Milestones 1 and 2 |
| 4 | None yet | None yet | Real runner and pilot configuration |
| 5 | None yet | None yet | Module specifications, sources, rubrics, rater workflow |
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
