# M5 saved-output diagnostic, shared review and source-fidelity preparation

Status: exploratory post-hoc saved-output analysis and offline engineering preparation. No new inference, model downloads, pressure tuning or sycophancy-v3. Independent human validation remains pending; numerical updating stays parked. All earlier evidence, including v1/v2 scores and suitability decisions, remains unchanged.

## Answer-content audit and results

[Audit records and full metrics](diagnostic/audit.json) inspect all318 responses with `exact-answer-content-v1`:234 retain their original categorical label meaning; all84 originally rejected responses recover by exact unique visible option text (43 BF16,41 quantized). Ambiguous0; still unscoreable0. No label/text collisions occur in any of the nine scenarios. Synthetic tests explicitly cover collisions with preserved label priority and duplicate-option ambiguity rejection. Case, punctuation and internal whitespace are never normalized; JSON schema, duplicate-key and permitted-fence rules are enforced.

[Report](diagnostic/report.md) displays all branch/turn accuracy, false endorsement and unrelated-error outcomes. Diagnostic metrics use actual conversations, including malformed ancestors, updated correction targets and grouped scenario pairs; no historical assistant text is replaced with a normalized label. All original values, statuses, options, acceptance methods/reasons and input hashes remain auditable. Raw/compact input, task/data/plan, source and scorer lineage appear in the audit. Replays are secondary; all primary-effect denominators remain nine scenarios.

| Measure | BF16 frozen primary | 4-bit frozen primary | BF16 diagnostic | 4-bit diagnostic |
| --- | --- | --- | --- | --- |
| Strict bare JSON label schema | 109/159 | 65/159 | unchanged | unchanged |
| Scoreability | categorical116/159 | categorical118/159 | content159/159 | content159/159 |
| Initial / final-neutral accuracy | 6/6 of9 each; full-set null | 6/6 of9 each; full-set null | 9/9 each | 9/9 each |
| Mild minus neutral | null, bounds[2/9,8/9] | null, bounds[3/9,8/9] | 8/9 | 8/9 |
| Confident minus neutral | null, bounds[1/9,6/9] | null, bounds[2/9,7/9] | 6/9 | 7/9 |
| Updated-source accuracy | 4/6 of9; bounds[4/9,7/9] | 3/6 of9; bounds[3/9,6/9] | 7/9 | 6/9 |
| Frozen suitability | failed | failed | no retrospective screen | no retrospective screen |

Frozen quantized-minus-reference contrasts remain null: mild bounds[-5/9,6/9], confident[-4/9,6/9], five complete scenario pairs each. Diagnostic contrasts are0 mild and1/9 confident, with9/9 complete scenario pairs. Diagnostic missing-data bounds collapse to their point values; floating-point representation is retained in JSON. These bounds are not confidence intervals. Exact-text/status and diagnostic-answer repeats are6/6 each. Recovered content enables this diagnostic observation; it does not validate the frozen protocol or identify quantization preservation, broad social pressure, or study readiness. Correction errors and discourse concerns remain.

## Discourse consistency

[Discourse audit](diagnostic/discourse.json) assesses all300 noninitial request occurrences across nine scenarios and the actual branch histories. Input-only concerns:36 scripted confident/correct turn2/3 slots presuppose disagreement without consulting an answer. Actual concerns:61 occurrences (57 main,4 replays) where the preceding assistant answer already endorses the stated belief. Main breakdown: BF16 confident14/correct16, quantized confident13/correct14. Each deployment adds one confident and one correct replay occurrence. These related occurrences are not independent observations.

Records contain exact user message, preceding raw response and diagnostic interpretation, scenario/branch/turn, stated belief and reason. “Earlier answer” may refer ambiguously to the initial answer; the audit flags a pragmatic concern, not a human-validated intention. Correct-belief examples can follow correct answers; false-belief examples can follow adoption. All fixed scripts remain unchanged. Suggested future history-neutral wording is “I am certain that [belief statement]” or “My firm belief is that [belief statement]”, followed by the factual question, omitting claims of disagreement. This proposal is not implemented or run.

## Shared review and source fidelity

[Sycophancy reviewer packet](sycophancy-review/packet.json) includes sources, questions/options, independent original/updated keys, complete conversations, diagnostic mappings and explicit rubrics for all318 responses. [Template](sycophancy-review/template.json) leaves human fields unset. Keep [analysis map](sycophancy-review/analysis-map.json) separate; explicit deployment identities are removed from reviewer materials and item order is shuffled with seed1701. Raw formatting, content and related trajectories can still reveal identity clues. This complete development export does not choose a held-out human subset or establish blinding effectiveness.

Imports validate stable IDs, task/packet/rubric versions, reviewer kind/identity and timezone-aware timestamps, reject unknown/duplicate IDs and incompatible versions, and use exclusive output files. Individual ratings, derived disagreements and referenced adjudications remain separate. [Workflow tests](workflow-tests) contain explicitly **synthetic-test** submissions, individual imports, one disagreement and a separate adjudication; none are human annotations. Human validation and study subset/rater design remain pending.

[Source-fidelity specification](../../SOURCE_FIDELITY.md), [synthetic fixtures](source-fixture/raw.json), [mechanical scores](source-fixture/scores.json), [review packet](source-review/packet.json), and [candidate configuration](../../../configs/source-fidelity-candidate-v1.json) prepare four fictional scenarios and nine synthetic responses. They cover supported/unsupported claims, insufficient sources, valid/invalid IDs, accurate/inaccurate and irrelevant quotations, empty responses and abstention. Semantic-support fields remain null; exact citation/quotation success is not entailment. Coverage and null zero-denominator rates prevent empty answers receiving unqualified perfect scores. Targets/annotations stay out of model-visible messages. No source-fidelity model inference occurred.

Remaining source decisions include fresh pilot documents/provenance, semantic endpoints and abstention costs, citation completeness/weighting, dedicated human subset/seed/weights/overlap/qualifications/budget, and model/backend/decoding/resource/competence/uncertainty configuration. No choices are silently resolved by fixture success.

## Verification and reproduction

[Verification](verification.json):4017 historical artifacts unchanged;12 files byte-identical in two fresh regenerations;11 saved derived artifacts match regenerated files; frozen primary metrics reproduce; source-fixture rescoring is identical. [Inventory](historical-hashes.json) was captured before edits and covers earlier evidence and saved artifacts. It includes local bulk paths, so complete historical verification needs this checkout's historical outputs; compact reconstruction and default tests require no bulk files, model files, network or accelerator. [Offline log](offline-tests.txt):47 tests passed. New focused tests cover exactness/collisions/ambiguity, all existing label interpretations, pairing, correction targets, missing bounds, immutable regeneration, blinding, review versions/IDs/timestamps, disagreements/adjudication and mechanical/semantic separation.

Root [README commands](../../../README.md#m5-saved-output-audit-and-review-workflow) were exercised for audit export, both review exports, source fixtures/rescoring, import/disagreement/adjudication and full verification. Destinations are exclusive; repeat with fresh paths. The original numerical synthetic fixture→score→report→rescore→regenerated-report workflow also succeeded in `/tmp/cib-m5-original-fixture/`; it does not reactivate numerical inference. Verification regenerations are in `/tmp/cib-m5-verification-new/`, with no inference calls or downloads.

Next concrete implementation: prepare the separately configured source-fidelity pilot planner, immutable attempt schema and saved-output report against this specification, after resolving its source/endpoint/budget decisions and freezing the common human subset design. Obtain independent human review of the current packets; no ratings are available to import yet. Calibration, replacement belief revision, counterargument representation, source-fidelity real pilot/validation, and other unfinished M5 packages remain pending. M5 is not complete.
