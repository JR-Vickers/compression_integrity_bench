# Decisions

## D001 — Offline implementation and artifact format

Status: accepted for Milestone 1, 2026-11-12. No superseded choice.

Use Python >=3.11, standard-library runtime/tests, JSON artifacts, and a Markdown report. Setuptools >=68 supplies packaging and the CLI entry point; source execution needs no build dependency. This keeps verification independent of networks, credentials, downloads, and accelerators. A single raw JSON artifact owns the planned request set, all one-attempt records, task snapshot, and manifest. Scoring and reporting are separate commands that create new files exclusively. Consequence: the fixture runner is intentionally small and has no production resume or retry functionality. These remain Milestone 3 work.

## D002 — Explicit development instrument and missing-data policy

Status: accepted only for development fixtures, 2026-11-12. No superseded choice.

Adopt the proposed self-contained pre/post numerical updating task to exercise the offline pipeline. Hand-author two base scenarios with three branches and two label variants. Each branch/variant has its own pre request; those repeated priors are engineering checks, not independent scenario samples. Both scenarios share a template cluster. Perfect response scripts use hand-entered probabilities; the scorer computes targets separately with exact fractions before float loss calculations. Computational rounding is not a behavioral acceptance threshold.

Use strict JSON probability parsing and distinguish malformed, refusal, truncation, infrastructure error, and valid numerical responses. Providers script stop-status metadata; a real adapter must later define its own mapping. Script the same planned set for both providers; never reprompt malformed answers. Average equal-weight conditions/label variants within scenario, then equal-weight scenarios. Each scenario metric requires complete eligible conditions; report coverage, complete-scenario posterior contrasts, and full-set conservative missing-loss bounds. Bounds use the global [0,1] posterior-loss range and can be wider than target-specific attainable bounds.

Consequences: these fixtures validate plumbing and scorer behavior only. They do not select a checkpoint, backend, study population, sample size, final endpoint weights, parser policy, or preservation margin. Direction and stability tolerances remain null. No empirical calibration, compression, or preservation claim is supported. Held-out study choices remain unresolved in METHODOLOGY.md.

## D003 — Existing document locations

Status: accepted, 2026-11-12. No superseded choice.

Keep project specifications in `docs/`, matching the existing repository and AGENTS.md links. PLAN.md's original instruction to place them all in the root was inconsistent with those paths; update the plan to describe the existing layout. The original proposal is absent; do not fabricate its content.
