# M4c: conditional interpretation, rule scaffolding and numerical evaluation

Exploratory instrument diagnostic, not held-out evaluation or a quantization comparison. Protocol saved before generation: [configuration](../../../configs/rule-diagnostic-v1.json), [fresh dataset](../../../src/cib/data/rule-diagnostic-v1.json), METHODOLOGY §19 and D010.

Only the existing Qwen/Qwen2.5-7B-Instruct original BF16 reference at revision `a09a35458c702b33eeacc393d103063234e8bc28`. Reuse `configs/reference-check-qwen25-7b.json`, `.cache/m4b-qwen25-7b/`, `outputs/m4b-7b-prepare-permitted/prepared.json` and `outputs/mlx-env/`. [Preparation copy](prepared.json) preserves the existing record, not a new preparation. No model/tokenizer/template/decoding/JSON requirement change.

Before generation:12 new numerical tuples, balanced/unequal prior × favors H/favors not H/uninformative, two each. A is M4b mathematical conditional wording; B adds only symbolic Bayes normalization; C supplies the full numerical expression, including unsimplified products and denominator. Targets are identical across forms and scorer-only. Formula provision and numerical substitution are deliberate task interventions. Six fixed repeats are c01 and c06 in all forms. Case order c01–c12, rotating ABC/BCA/CAB; repeats last.36+6=42 planned observations; hard maximum60 attempts including smoke/retries, no separate smoke. At most one later infrastructure retry/observation, no returned-output retries/exclusions/reprompts/expansion. Resource limits and stopping are in the frozen configuration.

Prespecified analysis: outer-json-fence-v1 unchanged, strict-format compliance separate; counts and failures; complete per-case target/response/error, MAE by form/type/cross, paired B−A/C−A/C−B errors, unchanged-prior baseline, repeatability. No pre requests: uninformative error is against the **stated prior**, not observed-pre drift. Trial0 only for main results;12 numerical problems/one template cluster, not36 or42 independent scenarios. Full means require all terms, missing scores stay missing with [0,1] bounds. M4b numerical screen per form:12/12 coverage, MAE≤0.05 and≤75% of baseline; uninformative stated-prior error≤0.02 (4/4). Earlier prior-reading/likelihood gates are inapplicable. Keep all continuous errors. Prespecified recommendation: A passes retain exploratory family pending held-out validation; A fails and B/C passes revise with scaffolded constructs distinguished; all fail park for comparison. No automatic further diagnostic/model.

## Results and complete per-case comparison

All **42/42 planned observations were attempted, completed at EOS and primary-scoreable**, one attempt each;36 main and6 repeats. Strict compliance **0/42** (0/12 main per form), because every response uses an outer JSON fence. Zero infrastructure failures, refusals, truncations, primary-malformed answers, unexecuted observations or retries.42 total generation attempts is below60. No smoke or extra responses.12 numerical problems in one template cluster remain the analysis units; no population uncertainty estimate.

| Form | Planned / attempted / completed / scoreable main | MAE | Uninformative prior MAE (4/4) | Unchanged-prior loss | Screen |
| --- | --- | ---: | ---: | ---: | --- |
| A | 12 / 12 / 12 / 12 | 0.09105243 | 0.13035714 | 0.11171051 | fail |
| B | 12 / 12 / 12 / 12 | 0.09317428 | 0.14583333 | 0.11171051 | fail |
| C | 12 / 12 / 12 / 12 | 0.18463727 | 0.08750000 | 0.11171051 | fail |

The unchanged-prior baseline is 0.11171051 across12/12 targets; the relative gate is 0.08378288. All forms have full coverage but fail each numerical gate: MAE≤0.05, MAE≤75% of baseline, and uninformative stated-prior error≤0.02. A/B improve over baseline, but insufficiently; C is worse than baseline. All [0,1] missing-loss bounds collapse to the observed MAE because coverage is complete.

Each response below is the primary parsed number; exact fenced raw text, prompt messages, actual rendered inputs/token IDs, attempt status and IDs are retained for all42 observations in [observations.json](observations.json). Full precision errors, pairing rows and scorer lineage are in [summary.json](summary.json). Display rounding does not change scoring.

| Case | Prior | P(E|H) | P(E|not H) | Exact target |
| --- | ---: | ---: | ---: | --- |
| c01 | 0.5 | 0.7 | 0.3 | 7/10 |
| c02 | 0.5 | 0.35 | 0.65 | 7/20 |
| c03 | 0.5 | 0.6 | 0.6 | 1/2 |
| c04 | 0.15 | 0.7 | 0.25 | 42/127 |
| c05 | 0.35 | 0.3 | 0.75 | 14/79 |
| c06 | 0.65 | 0.55 | 0.55 | 13/20 |
| c07 | 0.5 | 0.9 | 0.45 | 2/3 |
| c08 | 0.5 | 0.15 | 0.6 | 1/5 |
| c09 | 0.5 | 0.2 | 0.2 | 1/2 |
| c10 | 0.85 | 0.65 | 0.35 | 221/242 |
| c11 | 0.25 | 0.45 | 0.9 | 1/7 |
| c12 | 0.7 | 0.3 | 0.3 | 7/10 |

| Case | Target (decimal) | A response | A error | B response | B error | C response | C error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| c01 | 0.70000000 | 0.7000000000000001 | 0.00000000 | 0.67 | 0.03000000 | 0.5 | 0.20000000 |
| c02 | 0.35000000 | 0.35714285714285715 | 0.00714286 | 0.35714285714285715 | 0.00714286 | 0.5 | 0.15000000 |
| c03 | 0.50000000 | 0.5 | 0.00000000 | 0.5 | 0.00000000 | 0.5 | 0.00000000 |
| c04 | 0.33070866 | 0.21052631578947367 | 0.12018235 | 0.2647058823529412 | 0.06600278 | 0.5 | 0.16929134 |
| c05 | 0.17721519 | 0.2857142857142857 | 0.10849910 | 0.2857142857142857 | 0.10849910 | 0.46153846153846156 | 0.28432327 |
| c06 | 0.65000000 | 0.65 | 0.00000000 | 0.55 | 0.10000000 | 0.5 | 0.15000000 |
| c07 | 0.66666667 | 0.6666666666666666 | 0.00000000 | 0.6666666666666666 | 0.00000000 | 0.5 | 0.16666667 |
| c08 | 0.20000000 | 0.2142857142857143 | 0.01428571 | 0.2142857142857143 | 0.01428571 | 0.5 | 0.30000000 |
| c09 | 0.50000000 | 0.25 | 0.25000000 | 0.25 | 0.25000000 | 0.5 | 0.00000000 |
| c10 | 0.91322314 | 0.782608695652174 | 0.13061444 | 0.7948717948717949 | 0.11835135 | 0.55 | 0.36322314 |
| c11 | 0.14285714 | 0.3333333333333333 | 0.19047619 | 0.3333333333333333 | 0.19047619 | 0.375 | 0.23214286 |
| c12 | 0.70000000 | 0.42857142857142855 | 0.27142857 | 0.4666666666666667 | 0.23333333 | 0.5 | 0.20000000 |

## Problem types and paired changes

All main type terms are complete. Prior-type subsets have6 cases each, evidence-type subsets4 each, and each crossed subset2. Means weight the eligible problems equally; repeated forms do not add independent problems.

| Type | Problems per form | A MAE | B MAE | C MAE | Unchanged-prior loss |
| --- | ---: | ---: | ---: | ---: | ---: |
| balanced | 6 | 0.04523810 | 0.05023810 | 0.13611111 | 0.13611111 |
| balanced/favors_h | 2 | 0.00000000 | 0.01500000 | 0.18333333 | 0.18333333 |
| balanced/favors_not_h | 2 | 0.01071429 | 0.01071429 | 0.22500000 | 0.22500000 |
| balanced/uninformative | 2 | 0.12500000 | 0.12500000 | 0.00000000 | 0.00000000 |
| favors_h | 4 | 0.06269920 | 0.05358853 | 0.22479529 | 0.15264962 |
| favors_not_h | 4 | 0.08010096 | 0.08010096 | 0.24161653 | 0.18248192 |
| unequal | 6 | 0.13686677 | 0.13611046 | 0.23316343 | 0.08730991 |
| unequal/favors_h | 2 | 0.12539840 | 0.09217706 | 0.26625724 | 0.12196590 |
| unequal/favors_not_h | 2 | 0.14948764 | 0.14948764 | 0.25823306 | 0.13996383 |
| unequal/uninformative | 2 | 0.13571429 | 0.16666667 | 0.17500000 | 0.00000000 |
| uninformative | 4 | 0.13035714 | 0.14583333 | 0.08750000 | 0.00000000 |

Paired differences are later-form absolute error minus earlier-form absolute error; negative favors the later form. All12/12 pairs per comparison are scoreable.

| Case | B−A | C−A | C−B |
| --- | ---: | ---: | ---: |
| c01 | 0.03000000 | 0.20000000 | 0.17000000 |
| c02 | 0.00000000 | 0.14285714 | 0.14285714 |
| c03 | 0.00000000 | 0.00000000 | 0.00000000 |
| c04 | -0.05417957 | 0.04910899 | 0.10328856 |
| c05 | 0.00000000 | 0.17582418 | 0.17582418 |
| c06 | 0.10000000 | 0.15000000 | 0.05000000 |
| c07 | 0.00000000 | 0.16666667 | 0.16666667 |
| c08 | 0.00000000 | 0.28571429 | 0.28571429 |
| c09 | 0.00000000 | -0.25000000 | -0.25000000 |
| c10 | -0.01226310 | 0.23260870 | 0.24487179 |
| c11 | 0.00000000 | 0.04166667 | 0.04166667 |
| c12 | -0.03809524 | -0.07142857 | -0.03333333 |
| **Mean** | 0.00212184 | 0.09358484 | 0.09146300 |

## Repeatability and interpretation

All six fixed repeats are scoreable and match original text, status and probability exactly (maximum absolute difference0). Their probabilities: c01 A0.7000000000000001/B0.67/C0.5; c06 A0.65/B0.55/C0.5. Trial1 contributes no main score, baseline or independent scenario. Exact repeat records are in the summary and observations artifacts.

**Recommendation: park this numerical task family as a quantization-comparison endpoint for the current instrument/reference combination.** This follows the prespecified all-forms-fail rule; it does not reject numerical updating as a research topic. Preserve A/B/C as exploratory diagnostic instruments and preserve all negative results. Do not substitute the scaffolded tasks into the original endpoint or select a new model from these results.

Supplying the formula did not improve aggregate error (B−A +0.00212184). It improved c04 and c10/c12 errors but worsened c01 and c06; the mixed paired results remain visible. This offers no demonstrated aggregate benefit from explicit rule scaffolding in this sample. Formula provision measures a different construct even when outputs happen to match.

Direct numerical evaluation failed more strongly overall (C−A +0.09358484). Nine of12 C responses are0.5, including both balanced uninformative cases where0.5 is correct and unequal cases where it is wrong. Failures persist after both rule provision and numerical substitution, so a conditional-reading-only explanation is insufficient. Numerical computation and following the expression/response task remain concerns. All42 numbers parse under the primary protocol, so missingness or fence removal cannot explain the numerical errors. Universal strict-format failure remains a separate protocol issue. Short outputs do not reveal which operation, mapping or instruction was used internally.

There is no success-only-on-C pattern and no success across conditions. M4b established direct likelihood/prior reading competence on its clearer controls, not normalized updating competence. A keeps its mathematical packet wording but uses fresh tuples; B adds a rule, C removes the packet/conditional context and supplies arithmetic. Earlier7B mathematical error0.10703398 versus current A0.09105243 is not a matched improvement estimate because numerical cases differ. One template cluster,12 chosen problems, one checkpoint/backend and fixed greedy repeats cannot establish a general mechanism or empirical uncertainty calibration.

**Next dependency:** explicitly decide and specify a replacement or redesigned instrument, with an independently validated reference-competence requirement, before any further quantization comparison. The current numerical endpoint is parked; final instrument/model selection, held-out design, uncertainty estimation and preservation margins remain unresolved. No new model or diagnostic round was started.

## Verification, provenance and artifacts

Before generation, the saved no-inference plan, exact-fraction posterior-odds audit, full unsimplified expression audit and tokenizer-only rendering check passed. [Preflight](preflight.json) contains all12 independent exact answers, frozen file/plan hashes and existing preparation identity. [Rendering validation](render-validation.json) covers42/42 prompts; the current CLI reproduction produced identical rendered inputs to that saved pre-generation check. Dataset/config/source hashes are frozen in the run plan. Targets are computed only in analysis and never supplied to the adapter.

The existing artifact inventory matches the preparation record and all four official shard hashes/sizes;339 saved BF16 tensors, no conversion/quantization. Actual loaded metadata matches M4b for model configuration, tokenizer chat template/hash, EOS IDs,339 BF16 tensors and zero quantized modules. Every completed KV audit is BF16. Same MLX-LM0.32.2/MLX0.32.4, original tokenizer, temperature0/seed0,64 new tokens,2048 context acceptance and original EOS/response requirement. Greedy repeat equality is observed on this machine, not a cross-device determinism guarantee.

Generation/stream-writing time 37.41s; native MLX peak 15,364,419,116 bytes (15.364 decimal GB), below24GB. Excludes loading/hashing; operational observation, not throughput benchmark. No downloads, dependency changes or paid services. Local Metal access was permitted for generation; no sandbox generation failure occurred.

All32 standard-library offline tests passed before generation; all33 pass after adding the compact measured-evidence regression. Independent hand-calculated fractions, visible-prompt equivalence, freshness, grouping, scope/config/preparation constraints, missingness, pairing, failures, retry ceiling and immutable regeneration were checked. The original fixture CLI produced raw/scores/report at `outputs/m4c-offline-fixture/`. Final verification evidence is recorded in PLAN.md. An exhausted-plan invocation returned0 without importing MLX or producing another attempt.

[Saved-output verification](verification.json) confirms repeated scores and reports byte-identical, equal to original scores, actual rendering/token IDs correct, raw-stream equality, loaded precision/template matching M4b and all original artifacts unchanged. It checks1,797 historical files and131 files in the new run (excluding the lock). Historical hashes include the original M4 audited inventory, prior versioned evidence, both M4b diagnostic runs and existing7B preparation. Original streams, attempts and raw snapshots are unchanged. Scoring/report generation uses no inference.

Artifact locations (bulk outputs remain Git-ignored):

- Immutable plan/journals/streams/loaded metadata/snapshot/scores/full report: `outputs/m4c-rule-v1/`.
- Pre-generation instrument/provenance/historical inventory/rendered text and tokens: `outputs/m4c-preflight-v1/`.
- Regenerated scores/reports and verification: `outputs/m4c-verification-v1/`.
- Tokenizer-only reproduction of preflight rendering: `outputs/m4c-render-reproduction-v1/`.
- Fixture regression: `outputs/m4c-offline-fixture/`.
- Versioned compact measured records, full-precision scores, original preparation copy and verification: this directory.

## Exact reproduction commands

Run at the repository root. These invocations were exercised using existing artifacts/dependencies. Set `PYTHONPATH=src`. Creation is exclusive: audit/score/report/output destinations below already exist; choose fresh names to repeat. A fresh experiment uses one new run directory consistently; first save/validate its zero-call plan, then run the fixed allocation once. On the saved completed run the generation command returns0; it never replays responses. Local Metal permission is needed only for generation. The tokenizer-only commands use the existing MLX environment for Transformers but do not load MLX/model weights or access the network.

```sh
export PYTHONPATH=src
.venv/bin/python -m cib.runner run --rule-diagnostic --config configs/reference-check-qwen25-7b.json --prepared outputs/m4b-7b-prepare-permitted/prepared.json --run outputs/m4c-rule-v1 --deployment reference --limit 0
.venv/bin/python scripts/verify_m4c.py preflight --run outputs/m4c-rule-v1 --output outputs/m4c-preflight-v1
# Before first generation, validate tokenizer rendering in a new directory:
outputs/mlx-env/bin/python scripts/verify_m4c.py render --run outputs/m4c-rule-v1 --output outputs/m4c-render-reproduction-v1
outputs/mlx-env/bin/python -m cib.runner run --rule-diagnostic --config configs/reference-check-qwen25-7b.json --prepared outputs/m4b-7b-prepare-permitted/prepared.json --run outputs/m4c-rule-v1 --deployment reference --limit 42
.venv/bin/python -m cib.runner snapshot --run outputs/m4c-rule-v1 --output outputs/m4c-rule-v1/raw.json
.venv/bin/python -m cib.rule_diagnostic score --raw outputs/m4c-rule-v1/raw.json --output outputs/m4c-rule-v1/scores.json
.venv/bin/python -m cib.rule_diagnostic report --raw outputs/m4c-rule-v1/raw.json --scores outputs/m4c-rule-v1/scores.json --output outputs/m4c-rule-v1/report.md
# No inference: regenerate twice and verify unchanged historical/raw artifacts.
outputs/mlx-env/bin/python scripts/verify_m4c.py verify --run outputs/m4c-rule-v1 --output outputs/m4c-verification-v1 --historical-hashes outputs/m4c-preflight-v1/historical-hashes.json
mkdir -p outputs/m4c-offline-fixture
.venv/bin/python -m cib fixture --output outputs/m4c-offline-fixture/raw.json
.venv/bin/python -m cib score --raw outputs/m4c-offline-fixture/raw.json --output outputs/m4c-offline-fixture/scores.json
.venv/bin/python -m cib report --raw outputs/m4c-offline-fixture/raw.json --scores outputs/m4c-offline-fixture/scores.json --output outputs/m4c-offline-fixture/report.md
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

The original tokenizer-only preflight used the same rendering operations now exposed by `verify_m4c.py render`; that CLI reproduction was checked byte-for-byte against the pre-generation rendered-input file. `preflight` deliberately rejects a run that has already started generation; saved preflight files retain the original evidence. Use a fresh run for a new preflight. For offline rescore/report only, start at the saved raw snapshot and choose new output filenames.
