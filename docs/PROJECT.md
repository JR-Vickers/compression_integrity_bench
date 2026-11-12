# Compression Integrity Bench

Status: Working draft, v0.3; M4c closed, full-study choices remain provisional
Updated: 2026-11-12  
Purpose: Define the research objective, intended deliverables, and project boundaries.

This document captures the project direction in the original Cosmos Institute grant proposal and proposes a tractable first experiment. Proposed implementation and study choices are labeled explicitly. Empirical findings are retained in the linked evidence records; this specification is not a preregistration. The pilot is a development stage, not a replacement for the broader study.

## 1. Research objective

Compression Integrity Bench (CIB) investigates whether quantization changes the epistemic behavior of open-weight language models. It compares a reference deployment with compressed variants derived from the same checkpoint.

The central research question is:

> How does quantization affect a model's measured epistemic behavior, and how do those changes relate to changes in task competence?

The project is motivated by the possibility that conventional task scores may miss changes in how models express uncertainty, respond to evidence, handle social pressure, cite sources, or represent opposing arguments. Whether these changes occur, their direction, and their magnitude are empirical questions.

Here, "epistemic integrity" is an umbrella for specified observable behaviors. It is not a claim to measure internal beliefs, intentions, consciousness, or overall alignment.

## 2. Research scope

The broader benchmark covers five behavioral dimensions:

| Dimension | Behavioral question |
| --- | --- |
| Calibration and uncertainty | Do expressed probabilities and uncertainty correspond appropriately to correctness and available information? |
| Resistance to sycophancy | Does the model preserve evidence-supported answers under pressure to agree with a user? |
| Evidence-sensitive updating | Does the model revise answers appropriately when relevant evidence changes, while remaining stable under irrelevant information? |
| Source fidelity | Do claims, quotations, and citations accurately reflect the supplied or verifiable sources? |
| Counterargument representation | Can the model faithfully present a strong opposing argument without distortion or unsupported additions? |

These dimensions form the research program. Supporting all five is not a prerequisite for the first functioning release. Each requires its own task definitions, scoring validation, and limitations.

Questions for the eventual study include:

1. Which behaviors change under particular quantization configurations?
2. Are changes consistent across tasks, models, and quantization methods?
3. Do behavioral changes coexist with similar measured performance on selected capability controls?
4. Which observed differences can be attributed to quantization, and which remain confounded by deployment differences?
5. Can the resulting tests become reusable checks for compressed-model deployment?

An unchanged capability score alone does not establish that a behavioral change is independent of general capability loss. Claims about preservation require an explicit tolerance and sufficient measurement precision.

### 2.1 Relationship to the grant proposal

The original proposal is the historical record of the proposed research. This file describes the working scope; substantive departures should be recorded with a reason rather than silently incorporated into implementation.

The foundational outputs are a benchmark covering the five dimensions above, a static side-by-side comparison viewer, and a formal writeup. A reusable evaluation harness supports these outputs. The study should provide practical guidance for people deploying compressed open-weight models, while limiting conclusions to the configurations actually tested.

The proposal's suggested mechanism, involving low-magnitude weights or distribution tails, motivates a hypothesis. Establishing that mechanism is not a prerequisite for the behavioral study, and the report must not treat it as an established explanation of observed changes.

The proposal assigns algorithmic scoring to calibration and sycophancy, and human evaluation to a dedicated subset of the other three categories. Preserve this as the starting evaluation plan. Exact tasks, rubrics, sampling, and scorer validation belong in METHODOLOGY.md. Deterministic scoring of a controlled updating pilot does not establish the validity of automated scoring for broader belief-revision tasks. Any revised division between algorithmic and human evaluation needs an explicit rationale.

### 2.2 Provisional experimental scope

The proposal contains the following candidate matrix. These are planning inputs, not verified implementations or a frozen protocol.

| Component | Original proposal | Working status |
| --- | --- | --- |
| Models | Qwen3.6-27B (Dense), Qwen3.6-35B-A3B (MoE), Gemma 4 12B | Names reproduced from the proposal; exact checkpoints, availability, suitability, and final selection remain unresolved |
| Reference | FP16 deployment | Retain a reference for the same checkpoint; exact precision and feasibility must be specified |
| Compressed conditions | 8-, 4-, and 3-bit | Candidate coverage; each implemented configuration must be precisely identified |
| Quantization/inference paths | GGUF K-quants, AWQ, MLX | Candidate paths; define the quantization configuration and runtime separately for each condition |
| Compute | Consumer Apple silicon (M4 Max) for the MLX arm; rented GPUs for full runs | Resource plan from the proposal; compute budget and allocation remain unresolved |
| Controls | Matched prompts, fixed decoding, variance reports | Retain as study requirements, with unavoidable differences documented |

Do not assume every model, method, and bit width forms a supported or comparable combination. Establish feasibility and comparability before expanding the matrix. Backend or hardware changes may require separate comparisons or narrower claims.

Per-expert sensitivity analysis on an MoE model is a planned work package in the proposal. Its implementation depends on the final model selection and tooling. It is not required for the first functioning release. If the final study omits or materially changes it, record that scope change and its rationale explicitly.

The proposal's 13-week schedule is a planning reference: weeks 1-3 for taxonomy, prompts, references, and a pilot; weeks 4-9 for full evaluation; weeks 10-13 for MoE analysis and completion of the viewer and release. No start date or revised deadline is established here. PLAN.md should turn this into milestones based on actual progress and resources.

## 3. Proposed first study

Proposed starting point: evidence-sensitive updating in controlled synthetic scenarios, including explicit probability elicitation. Use this to build and validate the complete comparison pipeline before expanding the benchmark. This is an engineering and measurement pilot; the final benchmark still needs all five dimensions.

| Aspect | Proposed initial choice | Status |
| --- | --- | --- |
| Models | One instruction-tuned open-weight checkpoint with a reference deployment that fits available hardware | Exact model unresolved |
| Comparison | Reference precision versus one weight-quantized variant from that checkpoint | Precision and method unresolved |
| Backend | One backend supporting both deployments, with settings matched where possible | Backend unresolved |
| Tasks | Synthetic scenarios with explicit priors, likelihoods, and relevant or irrelevant evidence | Proposed pilot scope |
| Scoring | Deterministic numerical and categorical scoring before introducing model judges | Proposed pilot approach |
| Outputs | Paired response records, score differences, uncertainty summaries, and an inspectable report | Proposed release target |

This pilot measures adherence to a controlled updating task. A broader claim about calibration on real-world questions requires a separate task set with objectively scored answers and a validated probability-elicitation procedure.

If pilot results expose ambiguity, floor effects, ceiling effects, or measurement artifacts, revise the instrument and evaluate a new held-out set. Preserve the earlier pilot and explain the revision.

### 3.1 Current disposition after Milestone 4c

Milestones 1–4c completed the engineering pipeline, exploratory pilot and instrument diagnostics; they did not validate the evidence-sensitive belief-revision benchmark category. The **numerical Bayesian-updating family is parked as a quantization-comparison endpoint for the current reference and response protocol**, following the prespecified competence screen ([D010](DECISIONS.md#d010-outcome-and-consequences), [M4c evidence](evidence/m4c/README.md)). Its code, fixtures, configurations, protocol versions, raw data, scores and negative findings remain available as diagnostic assets. Historical findings are unchanged.

Evidence-sensitive belief revision remains in the five-category benchmark scope alongside calibration and uncertainty, resistance to sycophancy, source fidelity and counterargument representation. Milestone 5 still needs a replacement belief-revision design and dedicated human-rated subsets for belief revision, source fidelity and counterargument representation. The next implementation work package is sycophancy specification and offline fixtures; [PLAN.md §11](PLAN.md#11-current-task-and-handoff) records the handoff. This ordering does not select a final model or validate another category.

## 4. Intended deliverables

### 4.1 Versioned benchmark tasks

Task definitions, prompts, answer keys, scoring rules, provenance, and limitations. Each task must state its intended construct and unit of analysis.

### 4.2 Reproducible evaluation harness

A lightweight pipeline that can:

- Run a pinned task set against a named deployment configuration.
- Retain raw requests, responses, errors, and deployment metadata.
- Score saved responses without repeating inference.
- Compare matched reference and compressed runs.
- Resume interrupted runs without silently duplicating or replacing observations.

### 4.3 Behavioral comparison viewer

A simple static report or viewer showing aggregate results and paired examples. Readers should be able to inspect improvements, regressions, unchanged cases, and failures. A hosted service is unnecessary for the initial release.

### 4.4 Formal research writeup

A formal writeup describing the research question, experimental configuration, results, uncertainty, scorer validation, confounds, and limits on generalization. A pilot report is an intermediate output. Null results and improvements are valid outcomes.

The proposal calls for a GitHub release under the MIT License and a public call for replication. Retain MIT as the intended license for original project code, while respecting separate terms for models, datasets, and other third-party materials. Release sufficient configurations, task definitions, scoring specifications, and permitted evaluation artifacts for others to inspect and reproduce the study.

## 5. Completion criteria

### First functioning release

- At least one fully specified task family runs through the complete pipeline.
- A real reference deployment and a corresponding compressed deployment have been compared.
- Every scored observation can be traced to its task, raw response, run configuration, and scorer version.
- Saved outputs can be rescored and the report regenerated without inference.
- Numerical targets and scorer behavior have been checked against independent examples.
- Failures and missing observations appear in the comparison report.
- The report clearly labels synthetic fixtures, exploratory pilot results, and any held-out results.
- Another user can reproduce the documented workflow with access to the required model and hardware.

### Initial study

- All five behavioral dimensions are represented by specified tasks and validated evaluation procedures.
- The study has a recorded protocol and a frozen evaluation set.
- Its experimental matrix and sample size are justified by the intended claims and resource budget.
- Scoring and any human or automated judging have been validated.
- Estimates include their denominators, uncertainty, and relevant sensitivity analyses.
- Claims distinguish the tested configuration from other models, backends, and quantization methods.

Finding degradation is not a completion criterion. An invalid or insufficiently sensitive instrument must not be presented as evidence of preservation.

The proposal's ambition is a concise, useful comparison of capability retention and epistemic behavior retention. A retained-headroom statistic is a candidate presentation, not a mandatory metric: its baseline, ceiling, direction, and interpretation must be defensible before use. Do not construct a headline number or universal score simply to match the proposal's illustrative example.

## 6. Development approach

Build a complete small experiment before expanding the matrix. Prioritize measurement validity, traceability, and the ability to inspect behavior.

Keep task definitions, inference, scoring, and reporting separable so that changing a scorer does not require rerunning models. Store scientific choices in explicit configurations and specifications rather than implicit defaults.

Prefer existing evaluation and inference infrastructure where it satisfies the requirements. Integration with lm-evaluation-harness and local inference tooling is a candidate, not an architecture decision already made. Introduce abstractions when a concrete second use requires them.

The reference and compressed deployments should be feasible on available hardware. A small model is an acceptable starting point for the pilot; it does not automatically determine the final study population. A restricted experiment with credible controls is more useful than an extensive matrix whose confounds cannot be interpreted.

## 7. Initial exclusions and later extensions

The first release does not require:

- A universal integrity score or deployment certification.
- A public leaderboard or hosted evaluation service.
- Training or fine-tuning new models.
- Exhaustive coverage of quantization methods and bit widths.
- Mechanistic localization of behavioral changes.
- A production monitoring platform.

The main study's broader model and precision coverage and planned MoE analysis are described in Section 2. Additional extensions beyond the proposal may include activation or KV-cache quantization, other quantization configurations, and further task families. These require a scientific justification and resource assessment before inclusion.

## 8. Documentation responsibilities

[METHODOLOGY.md](METHODOLOGY.md) owns task construction, controls, scoring, analysis, and interpretation. This document owns purpose, scope, and deliverables. AGENTS.md owns instructions for development agents; PLAN.md owns implementation milestones and current progress. These companion documents may be added incrementally.

When implementation planning documents are added, they should track the work required by these specifications. Architecture notes describe the chosen implementation; a decision log preserves the reasoning behind consequential choices.

Routine engineering details can be resolved during development. Changes to the measured construct, scoring targets, study population, exclusions, or evidence standard must be made explicitly in the relevant specification and recorded with their rationale.

## 9. Open decisions

1. Final study model selection and reference precision remain unresolved. Milestone 2 selected a local feasibility pair only: Qwen2.5-1.5B-Instruct BF16 versus its direct MLX 4-bit derivative; see [D004](DECISIONS.md#d004--local-pilot-deployment-pair). This does not freeze the study population.
2. Quantization method, configuration, and artifact provenance.
3. Backend and available hardware or compute budget.
4. Replacement belief-revision design and final task generators/wording across modules.
5. Future module pilot sizes, held-out study size, and allocation across conditions.
6. Primary endpoints, aggregation weights, and practically meaningful tolerances.
7. Evaluation designs and remaining module order after the next sycophancy preparation work package.
8. The scope of the pilot report and viewer, and the final study's release requirements.
9. Feasibility and scope of the planned MoE expert sensitivity analysis.

These choices do not prevent building fixtures, schemas, scoring functions, and a mock end-to-end pipeline. They must be explicit before results are used to support study conclusions.
