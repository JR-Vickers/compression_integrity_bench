# Offline pipeline architecture

This note describes Milestone 1 only. No real model integration exists.

`tasks.py` loads the versioned development task contract, validates probabilities and positive evidence denominators, enumerates scenario/condition/label cases, calculates exact-fraction targets, and renders self-contained requests. `pipeline.py` gives both scripted deployments identical model-visible inputs, records their supplied outputs and stop statuses, and saves `raw.json`. `scoring.py` reads saved records, verifies the complete planned set and identities, parses probabilities, computes independent losses, and aggregates within scenarios. `report.py` combines saved raw records and scores into escaped static Markdown. `cli.py` exposes `fixture`, `score`, and `report` commands.

## Records and ownership

All JSON has explicit schema versions. Nested scenarios and conditions inherit `cib.fixture.v1` and the task/dataset versions; their IDs are scoped by those versions. Their contract includes provenance, split, construct, grouping, protocol, inputs, and development analysis policy. Likelihoods and priors are model-visible facts. Annotations and derived posterior targets are scorer-only metadata. `request.input` is the **entire provider-visible payload**, containing messages alone; its serialized shape is tested against an allowlist. The raw artifact and manifest are audit records and must never be supplied wholesale to a real model.

- `cib.run.v1`: a raw artifact containing dataset, manifest, requests, and attempts. It is written with exclusive creation and never edited by scoring/reporting.
- `cib.manifest.v1`: run UUID, UTC timestamp, source fingerprint, Git revision/tree state (unknown revision when unavailable), Python/hardware, dataset hash, full scripted provider configuration, deployment registry, and explicit analysis choices. Seeds, decoding/output limits, and retry policy are recorded on requests; inapplicable settings are labeled. No weights/tokenizer/hardware inference precision exists for the scripted provider.
- `cib.deployment.v1`: deployment ID, synthetic kind, provider version/script hash, and explicit inapplicable model properties. IDs cannot masquerade as real reference/compressed deployments.
- `cib.request.v1`: deployment ID, scenario/cluster, task version, condition, label variant, prompt variant, trial, stage, exact model-visible input, input hash, and decoding. Request IDs hash deployment, complete pairing key, actual input, and decoding. Pairing keys omit deployment, but both sides must have distinct declared deployment IDs, identical key sets, identical inputs, and identical decoding.
- `cib.attempt.v1`: request/deployment ID, attempt index, timestamp, exact raw output (null when no output), supplied status, stop reason, and error. The fixture has exactly one attempt per request, including scripted infrastructure failures. No failure is removed from the planned set.
- `cib.scores.v1`: raw file hash, run/dataset identity, scorer version/source fingerprint, analysis configuration, per-request `cib.score.v1` parse/status records, per-condition `cib.condition-score.v1` diagnostics and independent targets, per-scenario coverage/metrics/bounds, and a paired comparison. Each condition score retains its pre/post request IDs. Parser behavior is versioned together with the scorer.

Raw validation rejects changes to supported fixture definitions, mismatched deployment identities, missing/duplicate planned requests or attempts, altered inputs, and inconsistent attempt ownership. This implementation supports the pinned v1 fixture; changing the instrument requires a new supported version. It is not a general experiment configuration runner yet.

## Derived artifacts and missingness

Rescoring creates a new scores file with source and raw lineage. Report generation verifies that saved scores belong to the exact raw file/run/dataset/configuration and displays both artifact hashes. All commands refuse to replace existing destinations. Files can still be manually edited outside this tool; hashes provide lineage checks, not tamper-proof storage.

Missing probabilities remain null. Prior/posterior losses can be scored independently; update and drift diagnostics require both stages. Drift is eligible only for uninformative conditions. Each metric's scenario mean requires all eligible conditions/variants. A posterior contrast is shown for complete paired scenarios; the full planned-set contrast is withheld unless all scenarios are complete. Conservative full-set contrast bounds preserve observed losses and use [0,1] for missing posterior losses, without renormalization. No bootstrap or other inferential uncertainty is implemented.

The static report exhaustively includes all fixture pairs and failures. Raw content is escaped inside text blocks. New response production varies timestamps/UUIDs; rescoring the same saved raw bytes with the same scorer produces identical score bytes. Regeneration never invokes the response producer. Default unittest checks run offline using independent analytic examples and temporary artifact directories.
