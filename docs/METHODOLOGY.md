# Compression Integrity Bench: Methodology

Status: Working draft, v0.2; proposed defaults require explicit study configuration  
Updated: 2026-11-12  
Companion: [PROJECT.md](PROJECT.md)

This document proposes an initial experimental protocol and defines measurement requirements for development. The broader research objective is established; the specific pilot, metric choices, and analysis defaults below remain proposals until recorded in a study configuration. No experiment or scorer validation is implied to have been completed.

PROJECT.md defines the full study scope, including all five behavioral dimensions, the comparison viewer, formal writeup, and planned MoE analysis. The numerical updating pilot below is the first development stage. Its metrics do not substitute for the remaining categories or the proposal's human-rated subset.

## 1. Measurement objective

Compare observable epistemic behaviors between a reference deployment and compressed variants derived from the same model checkpoint. Estimate changes separately for each task and behavioral dimension.

A reference deployment is a comparator, not a ground-truth oracle. Score both deployments against independently specified answers or rubrics. Matching an incorrect reference answer is not evidence of integrity.

The initial comparison targets weight quantization. Other changes, including activation precision, KV-cache precision, templates, and inference backends, must be held fixed where possible or disclosed as additional interventions.

## 2. Experimental units and pairing

A base scenario is the underlying problem or source material. Its evidence branches, pressure conditions, paraphrases, and conversation turns are related observations.

Every deployment receives the same eligible scenarios and assigned conditions. Pair observations by scenario, task version, condition, prompt variant, and trial index. Matching seed values do not guarantee matching random draws across implementations.

Use base scenarios as the default independent units for aggregation and uncertainty estimation. Preserve dependencies among their branches and turns. If several scenarios are generated from a common template or source and are strongly dependent, define a higher-level cluster or restrict claims to the sampled templates. Repeated generations of one prompt do not create new independent scenarios.

For deployment-level comparisons, the intervention unit is the deployment configuration. A large number of prompts on one checkpoint does not support population-wide claims about all models.

## 3. Reference and compressed deployments

### 3.1 Reference deployment

Use the source checkpoint in its intended non-quantized inference precision, normally BF16 or FP16 when supported. Record exact artifact and code revisions. Do not describe an 8-bit comparator as an unquantized reference.

If the intended reference cannot fit available hardware, select a smaller model, obtain suitable compute, or explicitly narrow the comparison to two compressed deployments. A changed comparator changes the research question.

### 3.2 Quantized deployment

Derive the quantized artifact from the same checkpoint or verify a third-party artifact's lineage. Record method, implementation version, bit widths, group size, calibration-data provenance where applicable, exclusions, mixed-precision layers, and artifact identifiers. Mark unavailable provenance as unknown.

Quantizer calibration data and benchmark evaluation data must be separate. Do not use held-out benchmark prompts to tune the quantizer or choose a favorable configuration.

For the proposed first comparison, keep activations and KV-cache settings the same where technically possible. If a backend couples these settings to weight quantization, record that coupling and limit attribution accordingly.

### 3.3 Matching and confounds

Match tokenizer, chat template, system instructions, rendered messages, context limits, output budget, stopping rules, and decoding policy. Record actual tokenized inputs when available.

Prefer the same backend and device class for both conditions. Quantization-specific kernels may still differ; document what the deployment intervention includes. When different backends are necessary, use a reference-precision cross-backend check where feasible. Without adequate controls, describe the result as a deployment comparison rather than an isolated quantization effect.

### 3.4 Expanding the matrix and the planned MoE analysis

The grant proposal's model names, 8/4/3-bit targets, and GGUF K-quants/AWQ/MLX paths are candidates recorded in PROJECT.md. Verify checkpoint availability, artifact lineage, supported precision settings, and reference feasibility before selecting conditions. A nominal bit width alone does not identify a comparable intervention. Use a condition registry with an explicit status and reason for unsupported or excluded combinations; an unsupported condition is not a completed result.

The planned per-expert MoE study needs a separate configuration after the main pipeline is validated. Specify which experts and tensors change, what remains at reference precision, and whether the experiment measures perturbation sensitivity or selective-precision allocation. Keep expert-selection data separate from held-out evaluation data. Compare allocation strategies at a matched precision or memory budget where that is the intended question, and report routing or other stack changes when measurable. Do not infer a mechanism from a behavioral association alone. If the final model selection removes the MoE arm, record the departure from the proposal.

## 4. Task specification contract

Every task family must define:

| Field | Requirement |
| --- | --- |
| Construct | Observable behavior and the claims it is intended to support |
| Population | Scenario distribution, language, and sampling procedure |
| Provenance | Source, generator, licenses, and revisions |
| Grouping | Base scenario ID, template/source cluster, and related variants |
| Inputs | Exact messages, evidence conditions, and conversation protocol |
| Targets | Independent answers, numerical targets, or explicit rubric |
| Elicitation | Output format and meaning of any requested probability |
| Scoring | Parser, metric, direction, aggregation, and missing-data rules |
| Validation | Gold fixtures, human checks, and known failure modes |
| Split | Development, pilot, or held-out evaluation assignment |

Keep scorer-only targets and annotations out of model-visible inputs. Explicit priors and likelihoods are legitimate inputs for an updating task; the calculated posterior answer is scorer metadata.

## 5. Proposed pilot: evidence-sensitive updating

### 5.1 Scenario design

Use synthetic binary-hypothesis scenarios with an explicit prior and known likelihoods. Clearly state the evidence-generation process and any conditional-independence assumptions. Avoid requiring obscure world knowledge.

For hypothesis H, prior p, and evidence E, the target is:

$$
p^* = P(H\mid E)
= \frac{P(E\mid H)p}{P(E\mid H)p + P(E\mid \neg H)(1-p)}.
$$

Example: with prior 0.5, P(E|H)=0.8, and P(E|not H)=0.2, the posterior is 0.8. With the same likelihoods and prior 0.2, it is 0.5. Uninformative evidence with equal likelihoods preserves the prior.

Generated cases must have valid probabilities and a positive evidence denominator. An impossible observed event has no defined posterior under the stated model and must not become an ordinary scored item. Validate targets independently, using exact fractions or suitable precision for fixtures, and distinguish scorer numerical tolerance from the behavioral tolerance for an acceptable answer.

Include evidence favoring either hypothesis, uninformative evidence, varied priors, and varied evidence strengths. Avoid a dataset in which the correct behavior is always to reverse an answer or always to stay near 0.5.

### 5.2 Conversation protocol

Elicit a probability before evidence and after a defined evidence condition. Use the same prompts for both deployments.

For the primary pilot, make the post-evidence request self-contained: restate the original scenario and new evidence without inserting a model-generated earlier answer. Treat pre- and post-evidence responses as paired stages. This holds the information supplied to each deployment fixed.

An optional secondary track can continue each deployment's own conversation. That measures the behavior of the entire evolving interaction; it also allows different earlier answers to affect later responses. Keep the two protocols separately labeled and scored.

Branch evidence conditions from the same initial scenario, rather than accidentally appending every condition into a single conversation. Label swaps and paraphrases must retain their scenario grouping.

### 5.3 Probability elicitation

Ask for P(H) on the interval [0,1], with an unambiguous definition of H. Prefer one stable structured format. A format example should not supply a plausible answer to the current question.

Freeze parsing rules after the pilot. Do not coerce out-of-range values, infer an unstated probability from prose, or repeatedly reprompt until a valid answer appears. If constrained decoding is used, apply the same constraints to both deployments and document them.

Verbalized probabilities and token probabilities are different measurements. Token-logprob analysis is optional and must specify its own answer-token mapping and normalization. Neither measurement alone establishes an internal belief.

### 5.4 Pilot endpoints

The proposed primary endpoint is absolute error against the analytic posterior, averaged within each base scenario across its predefined evidence conditions:

$$
L_i^{\mathrm{posterior}}
= \operatorname{mean}_{c} |\hat p_{ic,\mathrm{post}}-p^*_{ic}|.
$$

Report the same error for pre-evidence probabilities against their stated priors. Proposed secondary diagnostics are:

- Update error: |(p_hat_post - p_hat_pre) - (p_star_post - p_star_pre)|.
- Irrelevant-evidence drift: |p_hat_post - p_hat_pre| for uninformative evidence.
- Direction of revision, separating favorable, unfavorable, and zero-target changes.
- Format validity, truncation, and refusal rates.

Direction and stability diagnostics require a frozen numerical tolerance; this tolerance is unresolved. A zero-target update must not be scored as a required reversal.

These endpoints measure probability reporting and updating accuracy in a specified task. Analytic posterior error is not empirical calibration. Calculating a Brier score against a soft posterior target would also be a different quantity from the binary-outcome score in Section 6.1.

## 6. Broader behavioral modules

The complete benchmark must cover all five categories. The designs below are candidates for later implementation; each needs a full task specification and pilot validation before use in study conclusions.

| Category | Starting scoring plan | Required human role in the full study |
| --- | --- | --- |
| Calibration and uncertainty | Algorithmic probability scores and calibration diagnostics | Review task validity and audit ambiguous cases |
| Resistance to sustained sycophancy | Algorithmic answer and endorsement checks on objectively scoreable tasks | Validate that pressure and scoring measure the intended behavior |
| Evidence-sensitive updating | Analytic scores for controlled cases; rubrics for broader evidence-driven dialogue | Rate a prespecified dedicated subset of the broader tasks |
| Source fidelity | Mechanical citation/quotation checks plus support rubrics | Rate a prespecified dedicated subset for claim support and attribution |
| Counterargument representation | Rubric scores for fidelity and argument strength | Rate a prespecified dedicated subset using the source argument and rubric |

This preserves the proposal's division of scoring responsibilities. Automated judging can assist after validation; it does not silently replace the dedicated human evaluation. The subset size, allocation, and rater budget remain unresolved.

### 6.1 Calibration and uncertainty

Use questions with independently scored answers. Ask for the probability that a clearly identified answer is correct, and retain both answer and confidence. Define whether the answer was generated by the evaluated deployment or fixed externally; these support different comparisons. The distinction between answer confidence and predicting whether a question is answerable is discussed in [R1].

For binary correctness y_i and reported confidence c_i, use the explicit binary Brier convention:

$$
\mathrm{BS}=\frac{1}{N}\sum_i(c_i-y_i)^2.
$$

Its range is [0,1]; lower is better. This is the binary scaling documented in [R2]. Use reliability plots with fixed bin edges and bin counts as a separate calibration diagnostic. Brier score reflects more than calibration alone; a change in answer accuracy can change it.

Report accuracy, scoreable coverage, confidence, and probability scores together. For a generated-answer task, y_i refers to the exact answer whose confidence was elicited. For a fixed-proposition task, y_i instead encodes the truth of that proposition. Do not mix these conventions in one metric.

Any uncertainty or abstention track must define answerable and insufficient-information cases and a coverage-sensitive scoring policy. A system that refuses every question must not receive an unqualified top score.

### 6.2 Resistance to sycophancy

Use matched neutral and pressure conditions around objectively scoreable problems. A pressure condition introduces a user's unsupported stance or insistence while leaving the task evidence unchanged. Include correct and incorrect user stances and balanced answer positions. This adapts the general behavioral distinction studied in [R3].

Record accuracy in each condition and the pressure-associated change in endorsement of an incorrect user claim. Measure sustained pressure using a fixed script and turn budget, keeping the entire dialogue within one analysis cluster.

For an evolving dialogue, each deployment continues its own prior responses under the same scripted user interventions. The resulting histories may differ; report this as a conversation-level deployment comparison. A separate shared-history replay track can hold the entire input transcript fixed. Do not merge the two protocols. Prespecify whether the primary endpoint concerns the final turn, any false endorsement, or another dialogue summary, and report the complete scheduled scenario set. Analyses conditional on an initially correct response are secondary and must disclose the selection rule.

If the user's correction supplies valid new evidence, a revision may be appropriate and must not count as sycophancy. Courtesy, agreement on subjective preferences, and answer verbosity are not primary sycophancy endpoints.

### 6.3 Source fidelity

Begin with supplied documents and stable source IDs. Score whether a citation exists, whether it supports the attached claim, and whether quotations match the source. Citation count alone is insufficient.

Use explicit handling for unsupported claims, missing citations, and cases in which the provided sources cannot answer the question. Retrieval and browsing are separate interventions and are outside the proposed first pilot.

### 6.4 Counterargument representation

Provide source arguments and a rubric for their faithful, strong representation. Score coverage of central claims, omission of essential qualifications, distortion, and unsupported additions separately.

Use blinded human review to establish a defensible scoring standard before relying on automated judgments. Disagreement among qualified raters is measurement uncertainty to report. Treat this module as exploratory until the rubric is validated.

### 6.5 Broader evidence-sensitive updating

The numerical pilot in Section 5 supplies exact targets for a restricted task. Extend it with controlled source packets or dialogues containing relevant counterevidence, irrelevant assertions, and unsupported pressure. Independent annotations should identify what the evidence supports and the justified direction or range of revision. The human-rated subset should evaluate both responsiveness to valid evidence and stability under unsupported claims; a change of answer alone is not a success criterion.

## 7. Development, pilot, and held-out evaluation

Use three explicitly labeled stages:

| Stage | Permitted purpose |
| --- | --- |
| Development fixtures | Check formulas, schemas, parser behavior, and pipeline execution |
| Exploratory pilot | Diagnose task ambiguity, scorer validity, variance, feasibility, and floor/ceiling effects |
| Held-out evaluation | Estimate outcomes under a frozen protocol and report the planned analyses |

Split related templates, paraphrases, and source documents as groups when independence or generalization requires it. Randomly separating near-duplicate prompts is insufficient. Define and save the split before model-specific tuning.

Record generation seeds and generator versions. A development sample may be inspected freely. Once evaluation responses are inspected, changing prompts or scoring rules makes subsequent analysis exploratory unless evaluated on fresh held-out data. A documented correction to a genuine scoring bug must retain earlier versions and be applied symmetrically.

The held-out size is unresolved. Choose it using the smallest effect or equivalence margin of interest, expected variance, scenario dependence, and resource constraints. A handful of fixtures is enough for a smoke test and insufficient for a preservation claim. Do not stop sampling solely because a desired result appears.

## 8. Capability and deployment controls

Include simple controls for reading the stated prior, interpreting likelihoods, arithmetic, instruction following, and output-format compliance. A conventional capability benchmark can complement these controls when affordable; it does not replace them.

Analyze the full prespecified task set first. Report capability changes beside behavioral changes. Any subset based on observed success, including cases both deployments answered correctly, is a secondary conditional analysis and cannot establish independence from capability effects.

Compare changes using their original scales and uncertainty. Do not assert that epistemic behavior degrades "more" than capability by comparing unrelated score units without an explicit analysis model.

## 9. Inference protocol

Use a recorded decoding policy matched across deployments. A greedy run is a reasonable proposed pilot default. Repeating a deterministic call does not provide new task samples. A small repeatability check can identify backend nondeterminism.

If sampled decoding is studied, freeze temperature, sampling parameters, trial counts, and seed allocation. Average repeated trials within their scenario-condition or use a declared hierarchical analysis. Report finite-trial variability rather than treating every generation as independent.

Set output limits high enough for the prescribed response format and keep them matched. Record stop reasons and distinguish truncation from an incorrect answer. Freeze the use and visibility of any reasoning mode or reasoning budget; do not switch it between conditions.

Interleave deployment order where practical or record batching and order. Cache keys must include the deployment artifact, actual input, decoding configuration, and trial identity so outputs cannot leak between configurations.

## 10. Scoring, missing data, and judging

### 10.1 Deterministic scoring

Prefer exact answers and numerical targets where appropriate. Validate scorers using independently calculated cases, including label swaps, irrelevant evidence, extreme valid probabilities, invalid formats, and known wrong answers. Include simple baselines such as always returning the prior or 0.5 to test sensitivity.

Parser failures, valid but incorrect outputs, refusals, truncation, and infrastructure errors require distinct status labels. Save raw outputs before parsing. Any permitted normalization must be specified in advance.

### 10.2 Missing and invalid observations

Report requested observations, completed generations, valid responses, scoreable responses, matched scoreable pairs, and each failure category by deployment.

Infrastructure retries may follow a fixed policy; preserve attempt records. Do not give a model extra attempts solely because its answer was wrong or malformed. Empty or invalid output is not zero error, and absent scores must remain absent rather than becoming zeros.

For bounded pilot losses, report complete-pair estimates alongside conservative missing-data bounds over the full planned paired set. Assign missing losses their minimum or maximum possible value to bound the contrast, while retaining observed losses. These bounds concern the missing outcomes and are distinct from sampling confidence intervals. If missingness is large or asymmetric, restrict interpretation; a complete-pair result can be misleading.

Do not silently renormalize a scenario onto its easiest valid conditions. Report partial condition coverage and use the declared complete-scenario policy or bounds. A separate operational-success rate can capture formatting and generation reliability without pretending those failures have a measured probability error.

### 10.3 Human and model judges

Where rubric scoring is necessary, hide deployment labels, randomize response order, and keep the rubric fixed. Judge responses against the task and sources rather than against the reference model's answer.

Select the primary human-rated subset by a recorded random or stratified rule before inspecting condition differences. Use common sampled scenarios across compared deployments, retain the sampling seed and strata, and declare weights if estimating results beyond the sampled subset. Diagnostic examples selected for large regressions can be reviewed separately but must not determine the primary human estimate.

Proposed rater design: independent ratings with at least two raters on a prespecified overlap, a calibration exercise on separate development cases, and a documented adjudication procedure. Final overlap size, rubric scales, agreement summaries, and rater qualifications remain unresolved. Preserve individual ratings and disagreements before adjudication. Each rubric dimension needs explicit anchors and examples; additional prose or polished style must not automatically receive a higher fidelity score.

Validate automated judgments against an independent human-reviewed sample. Report disagreement, order sensitivity where relevant, and known systematic errors. Review a random or stratified sample across the score distribution as well as selected striking examples. Preserve judge prompts, versions, raw judgments, and adjudications.

The first numerical pilot does not require a model judge.

## 11. Aggregation and statistical analysis

Compute condition and trial summaries within each base scenario first. Specify equal or unequal condition weights before the held-out run. Give scenarios equal weight by proposed default, and keep task families separate. This prevents tasks with many paraphrases from dominating the report.

For a loss L, define the paired change as:

$$
d_i=L_{i,\mathrm{compressed}}-L_{i,\mathrm{reference}},
\qquad \Delta=\operatorname{mean}_i d_i.
$$

Positive Delta denotes degradation for loss metrics. For accuracy and other higher-is-better metrics, display the native direction explicitly; do not silently reuse the degradation sign convention.

Proposed uncertainty method: a paired cluster bootstrap with 95% percentile intervals, resampling independent base scenarios with all related observations intact. Use a higher cluster level if required by the sampling design. Record the seed, number of resamples, weighting, missing-data policy, and interval method. This default must be checked against the eventual design and sample size; it does not make a tiny pilot conclusive.

Report native-scale effects, reference and compressed estimates, sample counts, intervals, and failure rates. Stratified diagnostics can show evidence strength and task difficulty, but label unplanned analyses exploratory.

Select a small primary endpoint set before the study. If several formal hypothesis tests are used, specify the comparison family and multiplicity procedure. Report all planned configurations rather than selecting the largest regression.

A confidence interval containing zero does not establish preservation. A preservation claim requires a prespecified practically meaningful margin and an appropriate equivalence or noninferiority analysis. Those margins and analyses are unresolved. A descriptive statement that no difference was detected must include the precision and scope of the result.

### 11.1 Optional retained-headroom summaries

The proposal's headline retention statistic is optional. For a higher-is-better score S and a justified baseline B, a candidate retention ratio is (S_compressed - B) / (S_reference - B). Define the scoring direction, baseline, and any normalization before using it. The reference must have meaningful positive headroom over B; a near-zero denominator makes this summary unstable.

Always show original scores, denominators, uncertainty, and the definition of B. Do not silently clip improvements above 100%, unfavorable results, or undefined ratios. For losses, specify a defensible transformation or alternative definition rather than reversing a ratio ad hoc. Do not use these summaries to create a universal integrity score or to claim disproportionate epistemic harm without an explicit comparison design.

## 12. Reproducibility and run records

Each run must make the following information recoverable, with unknown values labeled:

- Run ID, timestamps, code commit, and working-tree state.
- Dataset/generator version, split, task IDs, grouping, and content hashes.
- Model/checkpoint revision, tokenizer, template, and model artifact identifiers.
- Quantization configuration and quantizer calibration provenance.
- Backend/build version, hardware, numerical precisions, and relevant kernel settings.
- Exact messages and rendered input where available.
- Decoding policy, seeds, output limits, stop rules, and reasoning configuration.
- Attempt-level raw output, status, stop reason, and retry history.
- Parser/scorer version, per-item results, and aggregation/analysis configuration.
- Judgment and human-review records when applicable.

Keep original inference outputs immutable. Parser fixes and new analyses create derived artifacts that retain their lineage. Rescoring and report generation must work without model access. Approximate stochastic reproducibility and exact reconstruction of analyses are different requirements; document both.

## 13. Interpretation and reporting

Report the tested checkpoint, task distribution, compression configuration, and inference stack prominently. Distinguish empirical findings, exploratory explanations, and broader hypotheses.

Synthetic updating tasks offer known targets but also test arithmetic, instruction following, and numerical reporting. Good performance there does not establish reliability in unrestricted dialogue. Real-world source and argument tasks introduce their own judgment uncertainty.

A single checkpoint or method cannot establish a universal relationship between compression and integrity. Sycophancy or source-fidelity changes cannot automatically be inferred from updating results. Mechanistic explanations require additional evidence.

Show representative paired cases and explain their selection. Include improvements and unchanged cases as well as regressions. Aggregate scores must remain traceable to the underlying responses.

## 14. Choices to resolve before a held-out study

| Decision | Current status |
| --- | --- |
| Checkpoint, reference precision, quantizer, and backend | Local feasibility pair recorded in [D004](DECISIONS.md#d004--local-pilot-deployment-pair); held-out study configuration remains unresolved |
| Scenario generator, evidence allocation, and task language | Synthetic binary updating in English proposed |
| Pilot and held-out sizes and grouping | Unresolved |
| Primary endpoint and condition weights | Posterior absolute error and equal weights proposed |
| Probability format, parser rules, and diagnostic tolerances | Unresolved |
| Sampling, trial counts, and repeatability checks | Greedy pilot proposed; study policy unresolved |
| Capability controls and cross-backend checks | Required in principle; concrete tasks unresolved |
| Uncertainty, multiplicity, and preservation margins | Cluster bootstrap proposed; final analysis unresolved |
| Human review plan for later rubric tasks | Unresolved |
| Full matrix feasibility and planned MoE expert intervention | Unresolved; maintain explicit condition and scope records |
| Retained-headroom definition and eligibility | Optional; unresolved |

Infrastructure work can proceed using explicit fixtures and provisional configurations. Do not turn these open research choices into invisible production defaults or describe provisional results as confirmatory findings.

## 15. Reference points

These sources inform terminology and candidate measurements. The CIB protocol above is a proposed design, not a replication or a claim that the sources validate its complete methodology.

- [R1] Kadavath et al. (2022), [Language Models (Mostly) Know What They Know](https://arxiv.org/abs/2207.05221). Background on eliciting answer confidence and distinctions among self-evaluation targets.
- [R2] scikit-learn, [brier_score_loss documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html), accessed 2026-11-12. Reference for the explicit binary Brier scaling; this citation does not prescribe a package dependency.
- [R3] Sharma et al. (2023; revised 2025), [Towards Understanding Sycophancy in Language Models](https://arxiv.org/abs/2310.13548). Background on agreement with user beliefs as a behavioral evaluation target.
