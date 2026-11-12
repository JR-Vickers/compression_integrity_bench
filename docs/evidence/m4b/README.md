# Milestone 4b: updating-instrument diagnosis

Exploratory follow-up to M4. Original raw records, scores and interpretation history are retained. The initial audit below was completed before new inference. Diagnostic outcomes and recommendation follow later in this document.

## Audit of all four likelihood-reading controls

All four ask for **P(signal|H)**: the probability of a signal among cases where H holds. The clause “not P(H|signal)” explicitly excludes the reverse conditional. No prior P(H) is supplied or needed to read the likelihood. Both H and not-H groups can have a signal; their stated conditional probabilities need not sum to one. No urn/source labels or swapped variants are assigned to these controls; their request metadata uses `label_variant=original`. The tabled answer comes from the stated H-group probability, independently of the answer-key field.

Each rendered input below is byte-identical across deployments, including source chat template and assistant prefix. Each response is an EOS completion. Extracted probability means only parsing the bare JSON or one allowed outer fence; it never means extracting from prose. Strict compliance is 0/4 per deployment; primary coverage is 4/4.

### likelihood-1

Intended quantity: `P(E|H), not P(H|E)`. Independent answer: **1/10 = 0.1**. Reading the supplied conditional directly requires no Bayes inversion or normalization.

Exact rendered prompt (both deployments):

````text
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
The signal probability given H is 0.1; the signal probability given not H is 0.6. Report P(signal|H), not P(H|signal). Return only a JSON object with exactly the key "probability" and a numeric value in [0,1].<|im_end|>
<|im_start|>assistant
````

| Deployment | Primary probability | Absolute error | Correct (1e-9 historical tolerance) | Primary coverage |
| --- | ---: | ---: | --- | --- |
| quantized | 0.166667 | 0.066667 | False | 1/1 |
| reference | 0.16666666666666666 | 0.0666666666667 | False | 1/1 |

quantized exact raw response:

````text
```json
{
  "probability": 0.166667
}
```
````


reference exact raw response:

````text
```json
{
  "probability": 0.16666666666666666
}
```
````

### likelihood-2

Intended quantity: `P(E|H), not P(H|E)`. Independent answer: **1/4 = 0.25**. Reading the supplied conditional directly requires no Bayes inversion or normalization.

Exact rendered prompt (both deployments):

````text
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
The signal probability given H is 0.25; the signal probability given not H is 0.6. Report P(signal|H), not P(H|signal). Return only a JSON object with exactly the key "probability" and a numeric value in [0,1].<|im_end|>
<|im_start|>assistant
````

| Deployment | Primary probability | Absolute error | Correct (1e-9 historical tolerance) | Primary coverage |
| --- | ---: | ---: | --- | --- |
| quantized | 0.4 | 0.15 | False | 1/1 |
| reference | 0.4 | 0.15 | False | 1/1 |

quantized exact raw response:

````text
```json
{
  "probability": 0.4
}
```
````


reference exact raw response:

````text
```json
{
  "probability": 0.4
}
```
````

### likelihood-3

Intended quantity: `P(E|H), not P(H|E)`. Independent answer: **1/2 = 0.5**. Reading the supplied conditional directly requires no Bayes inversion or normalization.

Exact rendered prompt (both deployments):

````text
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
The signal probability given H is 0.5; the signal probability given not H is 0.6. Report P(signal|H), not P(H|signal). Return only a JSON object with exactly the key "probability" and a numeric value in [0,1].<|im_end|>
<|im_start|>assistant
````

| Deployment | Primary probability | Absolute error | Correct (1e-9 historical tolerance) | Primary coverage |
| --- | ---: | ---: | --- | --- |
| quantized | 0.8 | 0.3 | False | 1/1 |
| reference | 0.8 | 0.3 | False | 1/1 |

quantized exact raw response:

````text
```json
{
  "probability": 0.8
}
```
````


reference exact raw response:

````text
```json
{
  "probability": 0.8
}
```
````

### likelihood-4

Intended quantity: `P(E|H), not P(H|E)`. Independent answer: **3/4 = 0.75**. Reading the supplied conditional directly requires no Bayes inversion or normalization.

Exact rendered prompt (both deployments):

````text
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
The signal probability given H is 0.75; the signal probability given not H is 0.6. Report P(signal|H), not P(H|signal). Return only a JSON object with exactly the key "probability" and a numeric value in [0,1].<|im_end|>
<|im_start|>assistant
````

| Deployment | Primary probability | Absolute error | Correct (1e-9 historical tolerance) | Primary coverage |
| --- | ---: | ---: | --- | --- |
| quantized | 0.8333333333333334 | 0.0833333333333 | False | 1/1 |
| reference | 0.8333333333333334 | 0.0833333333333 | False | 1/1 |

quantized exact raw response:

````text
```json
{
  "probability": 0.8333333333333334
}
```
````


reference exact raw response:

````text
```json
{
  "probability": 0.8333333333333334
}
```
````

## Implementation and target findings

No demonstrated defect was found in conditional direction, target construction, request pairing, scoring or probability parsing. Independent fractions reconstructed from **every exact main post prompt** agree with all 144 condition-score rows (72 per deployment), including prior, posterior, update and drift losses. All 172 cross-deployment request pairs agree in messages, decoding, actual rendered text and token IDs. Request/cache ownership checks pass. Likelihood control target fields and parsed values agree with the independent prompt audit. Consequently no scoring correction or historical relabeling is justified.

For main swaps, H explicitly changes from source A to source B, the prior complements, and the likelihoods exchange. Posterior targets complement accordingly. The scenario condition name remains the branch identity: after complementing H, “support” need not support the newly named H. This is intentional complementary-hypothesis pairing, not an answer-key reversal. It does mean these swaps do not isolate lexical-label bias.

The likelihood answers are not consistently any single plausible alternate target. For example 0.1/0.6 equals the first BF16 response, but the other controls do not all equal that ratio, its inverse or a posterior under a common stated prior. No such prior was supplied. A likelihood-ratio substitution, conditional reversal, negation sensitivity, notation confusion and over-applied arithmetic remain proposed explanations rather than established mechanisms.

## Main-task discrepancies inspected before new inference

Largest irrelevant drift per deployment (all primary-scoreable pairs; strict failures are the JSON fences):

| Deployment | Scenario | Labels | Stated prior | Both likelihoods | Pre | Post | Drift | Target posterior |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| reference | t1-s1 | swapped | 0.9 | 0.4 | 0.9 | 0.4 | 0.5 | 0.9 |
| reference | t3-s1 | swapped | 0.9 | 0.4 | 0.9 | 0.5 | 0.4 | 0.9 |
| reference | t2-s1 | swapped | 0.9 | 0.4 | 0.9 | 0.6 | 0.3 | 0.9 |
| reference | t3-s1 | original | 0.1 | 0.4 | 0.1 | 0.4 | 0.3 | 0.1 |
| reference | t3-s2 | original | 0.25 | 0.4 | 0.25 | 0.5 | 0.25 | 0.25 |
| quantized | t3-s1 | original | 0.1 | 0.4 | 0.9 | 0.4 | 0.5 | 0.1 |
| quantized | t3-s1 | swapped | 0.9 | 0.4 | 0.1 | 0.6 | 0.5 | 0.9 |
| quantized | t1-s1 | original | 0.1 | 0.4 | 0.1 | 0.4 | 0.3 | 0.1 |
| quantized | t1-s1 | swapped | 0.9 | 0.4 | 0.9 | 0.6 | 0.3 | 0.9 |
| quantized | t2-s1 | original | 0.1 | 0.4 | 0.1 | 0.4 | 0.3 | 0.1 |

Equal likelihoods make the event uninformative for the source: target posterior equals prior. Some outputs equal the likelihood 0.4 or its complement 0.6; others do not. That pattern supports investigating confusion between a signal probability and a source probability, but does not prove it. The largest BF16 drift occurs despite a correct pre answer. Quantized t3-s1 drift is measured relative to an already-wrong pre answer, so drift and posterior error have different interpretations there.

All **six** quantized nonzero prior-error observations are shown below. They are six requests but only two distinct visible prompts; each is repeated for support/oppose/irrelevant branches with no condition evidence in the pre input. BF16 reads both correctly.

| Scenario / label | Branch | Target prior | BF16 | 4-bit | Quantized prior loss |
| --- | --- | ---: | ---: | ---: | ---: |
| t3-s1 / original | support | 0.1 | 0.1 | 0.9 | 0.8 |
| t3-s1 / original | oppose | 0.1 | 0.1 | 0.9 | 0.8 |
| t3-s1 / original | irrelevant | 0.1 | 0.1 | 0.9 | 0.8 |
| t3-s1 / swapped | support | 0.9 | 0.9 | 0.1 | 0.8 |
| t3-s1 / swapped | oppose | 0.9 | 0.9 | 0.1 | 0.8 |
| t3-s1 / swapped | irrelevant | 0.9 | 0.9 | 0.1 | 0.8 |

Exact rendered original pre prompt (identical for all three branches and both deployments):

````text
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
A packet comes from source A or source B. H means its source is A. The prior P(H) is 0.1. No signal has been observed. Report P(H). Return only a JSON object with exactly the key "probability" and a numeric value in [0,1].<|im_end|>
<|im_start|>assistant
````

Quantized exact raw response:

````text
```json
{
  "probability": 0.9
}
```
````


Exact rendered swapped pre prompt (identical for all three branches and both deployments):

````text
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
A packet comes from source B or source A. H means its source is B. The prior P(H) is 0.9. No signal has been observed. Report P(H). Return only a JSON object with exactly the key "probability" and a numeric value in [0,1].<|im_end|>
<|im_start|>assistant
````

Quantized exact raw response:

````text
```json
{
  "probability": 0.1
}
```
````

Successful standalone prior controls use the four unswapped base priors 0.1/0.25/0.5/0.75, but no packet/source/hypothesis context. The standalone controls did not include 0.9: that swapped failure is compared with the matched urn/factory contexts, not with a successful standalone 0.9 control. Their exact prompts and raw responses are retained in the audit artifact; all eight outputs match the supplied prior. The 0.1/0.9 packet pre failures are absent in the urn/factory templates with the same numerical problems, and absent at 0.5/0.75 in the packet template. This is an observed context-by-value interaction in the quantized deployment. Label reversal alone cannot explain it, because both original and swapped packet prompts fail. A tokenizer/template mismatch is weakened by identical paired rendered inputs; arithmetic inability is weakened by direct prior and arithmetic control success. None of those controls proves competence in the longer context.

## Frozen fresh diagnostic

`configs/diagnostic-v1.json` / `src/cib/data/diagnostic-v1.json` were saved, validated offline and embedded in the run plan before generation. Three underlying packet problems, two complementary labels, two evidence conditions and separate pre/post requests are expressed in original, explicit mathematical and group-frequency natural language. Four likelihood controls have the same three variants. The first six main calls repeat once. Per deployment: 72 main +12 control +6 repeat =90; 180 planned across both deployments, hard maximum 200 attempts including retries. Related branches, labels, wordings and repeats stay grouped. This is fresh generation on exploratory diagnostic prompts, deliberately including the original failed wording; it is not held-out evaluation.

Decoding is unchanged: greedy temperature0/seed0, 64 new tokens, 2048 context acceptance, original tokenizer/template/EOS, BF16 KV. No constraints, answer repair, generated pre context, outcome-based stopping or malformed-answer retry. Primary parser is unchanged outer-json-fence-v1; strict compliance denominator includes all eligible EOS completions. Mean losses require complete eligible branches/labels within scenario, then equal scenarios; missing scores remain missing and posterior [0,1] bounds remain exposed. Continuous losses and all planned conditions are reported.

Before observing diagnostic outputs, the exploratory suitability screen required full coverage separately for mathematical and natural wording: likelihood ≥3/4 correct within 1e-6 numerical tolerance; mean prior error ≤0.01; irrelevant drift ≤0.02; posterior error ≤0.05 and ≤75% of unchanged-prior baseline. Failure by original BF16 triggers one separate larger unquantized-reference check, 56 identical clearer trial-0 prompts plus four repeats (60 planned, maximum100 attempts), with the same competence criteria. These are competence screens, not preservation margins.


## Fresh diagnostic results

All 180 planned wording calls executed and completed at EOS, one attempt each. Primary coverage is **90/90 per deployment**; strict compliance is **0/90 completed eligible responses each**. No missing, malformed primary output, refusal, truncation, infrastructure attempt or retry occurred. The sandbox GPU setup failure is retained separately and precedes any generation attempt. Actual generation allocation stayed below the200-call limit. All six repeats per deployment match exact text/status and probability (6/6 scoreable pairs, maximum difference0).

For each wording/deployment there are 24 main and four control responses, **28/28 primary-scoreable**, with 12/12 prior/posterior/update terms and 6/6 irrelevant terms across3/3 complete base scenarios. Baselines are independently calculated for all 12/12 post targets. Strict compliance is 0/28 each. Lower losses are better.

| Deployment | Wording | Likelihood correct/4 | Likelihood mean absolute error | Prior error | Posterior error | Update error | Irrelevant drift | Unchanged-prior posterior baseline |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| reference | original | 0/4 | 0.15000000 | 0.00000000 | 0.19423077 | 0.19423077 | 0.21666667 | 0.11346154 |
| reference | mathematical | 4/4 | 0.00000000 | 0.00000000 | 0.22339744 | 0.22339744 | 0.23333333 | 0.11346154 |
| reference | natural | 3/4 | 0.06250000 | 0.00000000 | 0.26506410 | 0.26506410 | 0.25000000 | 0.11346154 |
| quantized | original | 0/4 | 0.15000008 | 0.26666667 | 0.20811966 | 0.31068376 | 0.27777778 | 0.11346154 |
| quantized | mathematical | 4/4 | 0.00000000 | 0.00000000 | 0.20673077 | 0.20673077 | 0.20000000 | 0.11346154 |
| quantized | natural | 2/4 | 0.07500000 | 0.00000000 | 0.27756410 | 0.27756410 | 0.25000000 | 0.11346154 |

All mathematical likelihood answers are exact. Natural wording gets3/4 BF16 and 2/4 quantized; at target 0.25 both return 0.5, and quantized additionally returns 0.8 at target 0.75. Original controls reproduce M4 values exactly. Thus “cannot read conditional probabilities” is too broad; direct reading succeeds with mathematical wording. The new variants change notation, representation and the negated contrast together, so their separate contributions are unresolved.

All clearer-wording pre answers match their priors (12/12 terms each per deployment/wording). Quantized original d1 once again complements0.1/0.9 in both branch-specific pre requests (four failed pre requests); these failures disappear under both clearer wordings. This reproduces contextual sensitivity rather than a scorer artifact. BF16 prior reporting succeeds in every wording.

Despite those improvements, main posterior loss exceeds the unchanged-prior baseline in every wording/deployment. The wording changes that fix reading do not fix updating. In natural uninformative cases the small deployments return **0.4 in all 6/6 post responses each**, even though the target posterior varies with the prior; 0.4 is the supplied mark likelihood. This behavior is consistent with reporting the wrong quantity or neglecting the prior, but raw short answers cannot identify the internal calculation. Mathematical uninformative prompts also retain drift, weakening a purely prose-specific explanation.

Paired quantized-minus-BF16 changes, all 28/28 primary-scoreable per wording/deployment and 3/3 scenarios; positive means larger loss:

| Wording | Posterior | Prior | Update | Drift |
| --- | ---: | ---: | ---: | ---: |
| original | +0.01388889 | +0.26666667 | +0.11645299 | +0.06111111 |
| mathematical | -0.01666667 | +0.00000000 | -0.01666667 | -0.03333333 |
| natural | +0.01250000 | +0.00000000 | +0.01250000 | +0.00000000 |

Do not overstate absence of competence: on the relevant branch alone (6/6 targets and 6/6 primary-scoreable post responses per wording/deployment), the unchanged-prior loss is 0.22692308. BF16 original relevant loss 0.17179487 and mathematical0.21346154 are lower; natural0.28012821 is higher. The complete equal-condition result still fails because irrelevant drift is substantial. Relevant-only diagnostics are declared condition analyses, not a success-filtered replacement endpoint.

## Separately configured larger-reference check

Failure of BF16 under both clearer wordings triggered the one allowed check. Before generation, source/settings were fixed in `configs/reference-check-qwen25-7b.json`, with the same already-recorded competence gates and 56 exact mathematical/natural trial-0 inputs plus four repeats. **60/60 planned calls executed, completed and primary-scoreable**, one attempt each; strict compliance 0/60, no missingness or retries, below 100-call ceiling. All four repeats match exact text/status/probability (4/4 scoreable pairs).

Official [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) revision `a09a35458c702b33eeacc393d103063234e8bc28`, Apache-2.0, original BF16, same MLX-LM 0.32.2 / MLX 0.32.4 and local 64 GiB M4 Max. Saved weights total 15,231,271,888 bytes; all four safetensors shards match official LFS SHA-256/size. Header inventory: 339 BF16 tensors. Actual loaded inventory: 339 BF16 tensors, zero quantized modules; source config has no quantization. Every KV audit is BF16. No quantization/conversion was performed, no paid compute. [Provenance](reference-provenance.json) retains exact inventories, hashes, loaded metadata and pinned source identity. The initial sandbox download failed DNS resolution; the permitted download succeeded in a new preparation directory. Both records are preserved.

All 56 trial-0 inputs match the smaller BF16 in messages, decoding, rendered text and token IDs. Model weights/architecture/training and tokenizer artifact identity differ; this is a separate suitability check, not a size-only causal contrast and not a quantization comparison. Same model family limits but does not eliminate those confounds.

Per wording: primary coverage 28/28, strict0/28; 12/12 prior/posterior/update terms, 6/6 drift terms, 3/3 scenarios.

| Wording | Likelihood correct/4 | Prior error | Posterior error | Update error | Drift | Unchanged-prior baseline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mathematical | 4/4 | 0.00000000 | 0.10703398 | 0.10703398 | 0.07195767 | 0.11346154 |
| natural | 4/4 | 0.00000000 | 0.16241259 | 0.16241259 | 0.10000000 | 0.11346154 |

The larger reference passes the reading gates but **fails posterior and drift gates in both wordings**. Mathematical posterior loss 0.10703398 narrowly beats the baseline 0.11346154 but not the required 0.05 ceiling or 25% relative improvement; natural0.16241259 is worse than baseline. Drift remains0.07195767/0.10000000, above 0.02. Therefore this check does not justify simply replacing the reference.

Of the larger model’s relevant-evidence responses across the two clearer wordings, all balanced-prior cases are exact (4/4 scoreable), while none of the unequal-prior cases are exact (0/8, all scoreable). This descriptive pattern uses 1e-6 representation tolerance and is not a new competence gate. It supports a narrower problem with applying the update rule to unequal base rates, while leaving arithmetic versus rule application/quantity reporting unresolved.

Representative larger residuals: mathematical prior 0.9, likelihoods 0.2/0.8, target 9/13≈0.69230769, output 0.18; natural prior 0.1 with equal 0.4 likelihoods, target 0.1, output 0.25. Relevant balanced prior 0.5 with 0.8/0.2 produces the correct 0.8. All are primary-scoreable, strict failures due to fences. The first error equals prior×likelihood but is not the normalized target; a single product-like answer does not establish a universal calculation mechanism.

## Evidence assessment and recommendation

| Proposed explanation | Evidence supporting it | Evidence weakening it or unresolved distinction |
| --- | --- | --- |
| Reversed or defective answer key | None found | Four controls request P(E given H); independent answers/losses and 144 main rows agree with saved scores |
| Pairing, tokenizer or parser artifact | None found | All original 172 pairs and new 90 pairs match exact inputs; outer parser only removes allowed fences; larger 56 trial-0 inputs match too |
| General inability to read stated probabilities | Original controls fail 0/4 | Mathematical controls pass 4/4 for both small deployments, all clearer pre requests succeed; larger all reading controls succeed |
| Context/representation sensitivity | Quantized complements reproduce only in original packet wording; clearer wording fixes them; direct-control scores change | Several language/notation features change together; negation, frequency conversion and lexical effects are not separately identified |
| Confusing signal likelihood with source posterior / neglecting base rates | Both small models output0.4 for all natural irrelevant cases; larger relevant balanced cases succeed while unequal-prior cases fail | Other responses do not follow a single substitute formula; latent arithmetic/attention/rule-application mechanisms are not observable |
| Insufficient 1.5B competence | All small-model updating variants fail gates and full-set baseline | 7B improves but fails the same gates, so size increase alone is not an adequate demonstrated remedy |
| Stochastic noise or truncation | None in these runs | Fixed greedy repeats reproduce exactly; all 240 new responses EOS/scoreable; this does not guarantee determinism on other devices |

**Recommendation: perform one specifically identified further check before expanding the study.** Use a new exploratory version with matched unequal-prior problems and an equal-likelihood branch, comparing (a) the present mathematical conditional request, (b) the same request with the symbolic Bayes normalization rule supplied, and (c) direct evaluation of the corresponding numerical expression. Keep targets identical and scorer-only; providing a formula is an explicit task intervention. This tests whether errors persist when rule selection is removed, and whether arithmetic evaluation itself is the bottleneck. Do not run more models or quantize 7B at this stage.

The smallest already-supported wording change is to use direct mathematical likelihood-reading controls in the next exploratory instrument, keeping original controls as a diagnostic. Mathematical prior phrasing also prevents the observed quantized complement errors in this sample. Neither change validates the updating endpoint: preserve this version and require a fresh instrument check rather than retroactively fixing prompts, exclusions or scores. A replacement reference is not selected. The original historical 0/4 control counts and M4 numerical conclusions remain unchanged; the new evidence weakens a broad “cannot read likelihoods” interpretation and strengthens a context-dependent elicitation plus updating-competence diagnosis.

## Verification, cost and reproduction

All **240 new generation requests** are accounted for: 180 in the first diagnostic (limit 200),60 in the separate reference check (limit 100). Each has exactly one completed attempt, with primary coverage 240/240 overall, strict compliance 0/240, no missing/truncated/refused/primary-malformed outputs. All attempts retain exact input, streamed output, stop reason, deployment identity, grouping, trial and cache identity. Exhausted-plan invocations returned zero without loading MLX; no inference was repeated to rescore.

Generation/stream-writing time and native MLX peak: small BF16 **15.41 seconds /3.264 GB**, quantized **8.17 seconds /1.253 GB**,7B BF16 **44.62 seconds /15.362 GB** (decimalGB). These exclude startup/loading/hashing and are operational observations, not throughput benchmarks. Each figure covers the complete 90/90, 90/90 or 60/60 primary-scoreable request set respectively. Downloaded official 7B weights are 15.231 GB and no derivative was produced. Both experiments respected their configured resource ceilings.

All **29 offline tests passed**, without MLX, network, models or credentials. Independent expected answers cover all original likelihood targets, unequal-prior Bayes targets, complementary labels and irrelevance; tests recover facts independently from all three rendered representations to verify equivalent targets. Allocation, source validation, absence of quantization, separate single-reference scope, grouping, retry ceiling, incomplete-data withholding, raw immutability and report/score regeneration are checked. The original fixture workflow also remains working.

The two saved-output verification audits confirm byte-identical repeated scores and reports, equal numerical results to original scoring, raw/stream text equality and BF16 KV. They check **1,055 historical files unchanged** (original M4 run plus versioned M2/M3/M4 evidence), plus 547 wording-run and 185 reference-run files unchanged. Aggregate source fingerprints change as reporting code is added; those versions are retained and numerical equality is checked separately. [Wording verification](wording-verification.json) and [reference verification](reference-verification.json) contain exact hashes. No historical raw file, score, policy label or evidence report was altered.

Run from the repository root with `export PYTHONPATH="$PWD/src"`. These are exercised invocations. Output destinations are exclusive and already exist: choose new destinations to repeat the audit, score, report or experiment. Reusing a completed run generates zero calls. Generation requires local Metal access; preparation alone needs network for the official pinned files. No credential is needed.

```sh
# Re-audit original evidence without inference.
PYTHONPATH=src .venv/bin/python scripts/audit_m4b.py --output outputs/m4b-audit-reproduction-v1

# Initial diagnostic, existing pinned1.5B artifacts.
outputs/mlx-env/bin/python -m cib.runner run --diagnostic --run outputs/m4b-wording-v1 --deployment reference --limit 90
outputs/mlx-env/bin/python -m cib.runner run --diagnostic --run outputs/m4b-wording-v1 --deployment quantized --limit 90
.venv/bin/python -m cib.runner snapshot --run outputs/m4b-wording-v1 --output outputs/m4b-wording-v1/raw.json
.venv/bin/python -m cib.diagnostic score --raw outputs/m4b-wording-v1/raw.json --output outputs/m4b-wording-v1/scores.json
.venv/bin/python -m cib.diagnostic report --raw outputs/m4b-wording-v1/raw.json --scores outputs/m4b-wording-v1/scores.json --output outputs/m4b-wording-v1/report.md

# One separately configured larger unquantized reference.
outputs/mlx-env/bin/python -m cib.larger_reference --config configs/reference-check-qwen25-7b.json --artifacts .cache/m4b-qwen25-7b --output outputs/m4b-7b-prepare-permitted
outputs/mlx-env/bin/python -m cib.runner run --diagnostic --config configs/reference-check-qwen25-7b.json --prepared outputs/m4b-7b-prepare-permitted/prepared.json --run outputs/m4b-reference-7b-v1 --deployment reference --limit 60
.venv/bin/python -m cib.runner snapshot --run outputs/m4b-reference-7b-v1 --output outputs/m4b-reference-7b-v1/raw.json
.venv/bin/python -m cib.diagnostic score --raw outputs/m4b-reference-7b-v1/raw.json --output outputs/m4b-reference-7b-v1/scores.json
.venv/bin/python -m cib.diagnostic report --raw outputs/m4b-reference-7b-v1/raw.json --scores outputs/m4b-reference-7b-v1/scores.json --output outputs/m4b-reference-7b-v1/report.md

# Offline score/report regeneration and immutable-file audit.
PYTHONPATH=src .venv/bin/python scripts/verify_diagnostic.py --run outputs/m4b-wording-v1 --output outputs/m4b-wording-verification-v1 --historical-hashes outputs/m4b-audit-v1/original-hashes.json
PYTHONPATH=src .venv/bin/python scripts/verify_diagnostic.py --run outputs/m4b-reference-7b-v1 --output outputs/m4b-reference-verification-v1 --historical-hashes outputs/m4b-audit-v1/original-hashes.json
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Versioned compact evidence: [audit.json](audit.json), [summary.json](summary.json), [diagnostic-examples.json](diagnostic-examples.json), [reference-provenance.json](reference-provenance.json) and the two verification files. Complete original audit (all irrelevant cases and exact attempts): `outputs/m4b-audit-v1/audit.json`, historical file inventory `original-hashes.json`. Immutable new journals and snapshots: `outputs/m4b-wording-v1/` and `outputs/m4b-reference-7b-v1/`. Preparation provenance: `outputs/m4b-7b-prepare-permitted/`; failed sandbox preparation invocation: `outputs/m4b-7b-prepare/`. Full regenerated reports with every request, raw response, failure category, condition/scenario score and configuration are [wording report](../../../outputs/m4b-wording-verification-v1/report.md) and [reference report](../../../outputs/m4b-reference-verification-v1/report.md). Weights/caches/bulk outputs remain Git-ignored.

Milestone 4b is complete as an evidence-supported narrowing of the diagnosis. There is no demonstrated scoring defect to correct, wording changes repair specific reading failures but not the updating endpoint, and the one larger reference also fails the predeclared gates. The next concrete dependency is the formula-application-versus-arithmetic check specified above, in a new exploratory version. Model selection, final instrument, held-out sample size, uncertainty estimator and preservation margins remain unresolved. These controlled numerical results do not measure empirical uncertainty calibration.
